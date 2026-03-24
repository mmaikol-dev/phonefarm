import base64
import datetime
import json
import random
import re
import subprocess
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
MODEL_NAME = 'moondream:latest'
SPOTIFY_PACKAGE = 'com.spotify.music'
SPOTIFY_ACTIVITY = 'com.spotify.music/.MainActivity'
ARTIST_NAME = 'Wakadinali'
STREAMS_TARGET = 10
STREAM_SECONDS = 35
LOG_FILE = 'spotify_moondream_log.txt'
SCREENSHOT_PATH = 'spotify-moondream-screen.png'

# Screenshot-backed fallbacks for 1080x2400.
COORDS = {
    'home_tab': (100, 2328),
    'search_tab': (324, 2288),
    'search_field': (350, 124),
    'artist_result': (228, 263),
    'artist_follow': (884, 261),
    'song_rows': [
        (232, 655),
        (229, 807),
        (227, 951),
        (226, 1101),
        (226, 1254),
    ],
}

BOTTOM_NAV_CANDIDATES = {
    'home': [
        COORDS['home_tab'],
        (100, 2288),
        (140, 2288),
        (120, 2235),
    ],
    'search': [
        COORDS['search_tab'],
        (324, 2328),
        (300, 2288),
        (360, 2288),
        (324, 2235),
    ],
}


def log(message):
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    full_message = f'[{timestamp}] {message}'
    print(full_message)
    with open(LOG_FILE, 'a') as file:
        file.write(full_message + '\n')


def adb(args, *, capture_output=False, check=False, timeout=30):
    try:
        return subprocess.run(
            ['adb', *args],
            capture_output=capture_output,
            text=True,
            check=check,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        log(f'⚠️ ADB command timed out: adb {" ".join(args)}')
        # Kill any hanging adb processes
        subprocess.run(['adb', 'kill-server'], capture_output=True, timeout=5)
        time.sleep(1)
        subprocess.run(['adb', 'start-server'], capture_output=True, timeout=5)
        raise


def tap(x, y, label=''):
    if label:
        log(f'   👆 Tap: {label} ({x},{y})')
    adb(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(random.uniform(1.0, 1.8))


def type_text(text):
    log(f'   ⌨️ Type: {text}')
    safe_text = text.replace(' ', '%s')
    adb(['shell', 'input', 'text', safe_text])
    time.sleep(1.2)


def press_enter():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
    time.sleep(1.5)


def press_back():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_BACK'])
    time.sleep(1.2)


def human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))


def device_is_connected():
    result = adb(['devices'], capture_output=True, timeout=10)
    return any('\tdevice' in line for line in result.stdout.splitlines())


def wake_and_unlock_device():
    log('🔓 Waking and unlocking phone...')
    adb(['shell', 'input', 'keyevent', 'KEYCODE_WAKEUP'])
    time.sleep(1.0)
    adb(['shell', 'wm', 'dismiss-keyguard'])
    time.sleep(0.8)
    adb(['shell', 'input', 'swipe', '540', '1800', '540', '500', '250'])
    time.sleep(1.2)
    adb(['shell', 'svc', 'power', 'stayon', 'usb'])
    time.sleep(0.5)


def open_spotify():
    log('📱 Opening Spotify...')
    wake_and_unlock_device()
    adb(['shell', 'am', 'start', '-n', SPOTIFY_ACTIVITY])
    time.sleep(4)


def capture_screen(path=SCREENSHOT_PATH):
    with open(path, 'wb') as file:
        result = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], stdout=file, timeout=10)

    if result.returncode != 0:
        raise RuntimeError('Could not capture phone screen from ADB.')

    time.sleep(0.5)
    return path


def check_ollama_health():
    """Check if Ollama is running and model is loaded."""
    try:
        req = urllib.request.Request('http://127.0.0.1:11434/api/tags')
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())
            models = [model['name'] for model in data.get('models', [])]
            if MODEL_NAME not in models:
                log(f'⚠️ Model {MODEL_NAME} not loaded in Ollama')
                log(f'   Run: ollama pull {MODEL_NAME}')
                return False
            return True
    except Exception as e:
        log(f'⚠️ Cannot connect to Ollama: {e}')
        return False


def ask_moondream(image_path, prompt):
    with open(image_path, 'rb') as file:
        encoded_image = base64.b64encode(file.read()).decode('utf-8')

    payload = json.dumps({
        'model': MODEL_NAME,
        'prompt': prompt,
        'stream': False,
        'images': [encoded_image],
    }).encode('utf-8')

    request = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode('utf-8')
    except urllib.error.URLError as error:
        raise RuntimeError(f'Could not reach Ollama at {OLLAMA_URL}: {error}') from error

    decoded = json.loads(body)
    return decoded.get('response', '').strip()


def dump_ui():
    """Dump UI hierarchy with improved error handling."""
    remote_path = '/sdcard/window_dump.xml'
    
    # Wait for UI to settle
    time.sleep(0.5)
    
    for attempt in range(1, 6):
        # Clear previous dump to avoid stale data
        adb(['shell', 'rm', remote_path], capture_output=True, timeout=5)
        
        dump_result = adb(['shell', 'uiautomator', 'dump', remote_path], capture_output=True, timeout=10)
        
        # Check if file was created
        file_check = adb(['shell', 'test', '-f', remote_path, '&&', 'echo', 'exists'], capture_output=True, timeout=5)
        if 'exists' not in file_check.stdout:
            log(f'   ⚠️ UI dump attempt {attempt}: file not created')
            time.sleep(1.5)
            continue
        
        read_result = adb(['exec-out', 'cat', remote_path], capture_output=True, timeout=10)
        
        # Validate content
        if not read_result.stdout or len(read_result.stdout) < 100:
            log(f'   ⚠️ UI dump attempt {attempt}: empty or truncated data')
            time.sleep(1.5)
            continue

        xml_start = read_result.stdout.find('<?xml')
        if xml_start == -1:
            log(f'   ⚠️ UI dump attempt {attempt}: no XML declaration found')
            time.sleep(1.5)
            continue

        try:
            return ET.fromstring(read_result.stdout[xml_start:])
        except ET.ParseError as e:
            log(f'   ⚠️ UI dump attempt {attempt}: ParseError - {e}')
            time.sleep(1.5)

    log('   ⚠️ All UI dump attempts failed')
    return None


def iter_nodes(root):
    if root is None:
        return []
    return list(root.iter('node'))


def find_first_node(root, predicate):
    for node in iter_nodes(root):
        if predicate(node):
            return node
    return None


def node_resource_id(node):
    return node.attrib.get('resource-id', '')


def node_text(node):
    return node.attrib.get('text', '').strip()


def node_desc(node):
    return node.attrib.get('content-desc', '').strip()


def node_center(node):
    bounds = node.attrib.get('bounds', '')
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
    if not match:
        return None, None

    x1, y1, x2, y2 = map(int, match.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2


def node_clickable(node):
    return node.attrib.get('clickable') == 'true'


def find_node_by_resource_id(resource_id):
    root = dump_ui()
    return find_first_node(root, lambda item: node_resource_id(item) == resource_id)


def has_resource_id(resource_id):
    node = find_node_by_resource_id(resource_id)
    return node is not None


def screen_contains_text(*needles):
    root = dump_ui()
    if root is None:
        return False
    
    lowered_needles = [needle.lower() for needle in needles]

    return find_first_node(
        root,
        lambda item: any(
            needle in node_text(item).lower() or needle in node_desc(item).lower()
            for needle in lowered_needles
        ),
    ) is not None


def is_search_screen():
    """Check if current screen is Spotify search screen."""
    # Check using resource IDs
    if (has_resource_id('com.spotify.music:id/search_root') or
        has_resource_id('com.spotify.music:id/search_field_root') or
        has_resource_id('com.spotify.music:id/query')):
        return True
    
    # Check using text content
    return screen_contains_text(
        'what do you want to listen to?',
        'discover something new',
        'browse all'
    )


def find_search_tab_coords():
    root = dump_ui()
    if root is None:
        return COORDS['search_tab']
        
    node = find_first_node(
        root,
        lambda item: (
            'search, tab' in node_desc(item).lower()
            or 'search tab' in node_desc(item).lower()
            or (
                node_clickable(item)
                and node_text(item).strip().lower() == 'search'
                and (node_center(item)[1] or 0) > 2000
            )
        ),
    )

    if node is not None:
        coords = node_center(node)
        if coords[0] is not None:
            return coords

    return COORDS['search_tab']


def tap_bottom_nav(tab_name):
    candidates = BOTTOM_NAV_CANDIDATES[tab_name]

    if tab_name == 'search':
        x, y = find_search_tab_coords()
        candidates = [(x, y), *candidates]

    seen = set()
    unique_candidates = []
    for x, y in candidates:
        if (x, y) not in seen:
            seen.add((x, y))
            unique_candidates.append((x, y))

    for index, (x, y) in enumerate(unique_candidates, start=1):
        tap(x, y, f'{tab_name.title()} tab (candidate {index})')
        time.sleep(1.5)

        if tab_name == 'search' and is_search_screen():
            return True
        if tab_name == 'home':
            return True

    return False


def find_search_field_coords():
    for resource_id in (
        'com.spotify.music:id/query',
        'com.spotify.music:id/search_field_root',
    ):
        node = find_node_by_resource_id(resource_id)
        if node is not None:
            coords = node_center(node)
            if coords[0] is not None:
                return coords

    return COORDS['search_field']


def clear_search_query_if_needed():
    node = find_node_by_resource_id('com.spotify.music:id/clear_query_button')
    if node is not None:
        x, y = node_center(node)
        if x is not None:
            tap(x, y, 'Clear search')
            time.sleep(0.5)


def find_artist_row_coords():
    root = dump_ui()
    if root is None:
        return COORDS['artist_result']
        
    artist_name = ARTIST_NAME.lower()

    for node in iter_nodes(root):
        if node_resource_id(node) != 'com.spotify.music:id/row_root':
            continue

        title_match = False
        subtitle_match = False

        for child in node.iter('node'):
            if node_resource_id(child) == 'com.spotify.music:id/title' and artist_name in node_text(child).lower():
                title_match = True
            if node_resource_id(child) == 'com.spotify.music:id/subtitle' and 'artist' in node_text(child).lower():
                subtitle_match = True

        if title_match and subtitle_match:
            x, y = node_center(node)
            if x is not None:
                return max(120, x - 220), y

    return COORDS['artist_result']


def extract_json_block(text):
    match = re.search(r'\{.*\}', text, flags=re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def locate_element(image_path, description, fallback):
    prompt = f"""
You are looking at a Spotify Android screenshot sized 1080x2400.
Find this target: {description}

Reply with JSON only:
{{"found": true, "x": 123, "y": 456}}

Rules:
- Return the best tap point for the exact target.
- Use screen pixel coordinates.
- If unsure, return:
{{"found": false, "x": 0, "y": 0}}
"""

    answer = ask_moondream(image_path, prompt)
    data = extract_json_block(answer)

    if data and data.get('found') and 0 < int(data.get('x', 0)) < 1080 and 0 < int(data.get('y', 0)) < 2400:
        x = int(data['x'])
        y = int(data['y'])
        log(f'   🧠 Moondream located {description} at {x},{y}')
        return x, y

    log(f'   ⚠️ Moondream could not confirm {description}, using fallback {fallback[0]},{fallback[1]}')
    return fallback


def identify_screen(image_path):
    """Identify current screen with multiple detection attempts."""
    # Try UI Automator first (fast path)
    root = dump_ui()
    if root is not None:
        # Check resource IDs
        if has_resource_id('com.spotify.music:id/search_root') or has_resource_id('com.spotify.music:id/search_field_root'):
            return 'search'
        if has_resource_id('com.spotify.music:id/search_content_recyclerview'):
            return 'results'
        if has_resource_id('com.spotify.music:id/follow_button'):
            return 'artist'
        if has_resource_id('com.spotify.music:id/now_playing_bar_layout'):
            return 'playing'
    
    # Check text content
    if screen_contains_text('what do you want to listen to?', 'discover something new', 'browse all'):
        return 'search'
    if screen_contains_text(ARTIST_NAME, 'playlists', 'artists', 'songs', 'albums'):
        return 'results'
    if screen_contains_text(ARTIST_NAME, 'monthly listeners', 'popular', 'follow'):
        return 'artist'
    if screen_contains_text('jump back in', 'fresh new music', 'liked songs'):
        return 'home'
    
    # Check playback state
    if get_spotify_playback_snapshot()['playing']:
        return 'playing'
    
    # Fallback to vision model
    prompt = """
Look at this Spotify Android screenshot.
Respond with JSON only:
{"screen":"home"}

Valid screen values:
home, search, results, artist, playing, other

Pick the single best label.
"""
    try:
        answer = ask_moondream(image_path, prompt)
        data = extract_json_block(answer)

        if data and data.get('screen') in {'home', 'search', 'results', 'artist', 'playing', 'other'}:
            return data['screen']

        lowered = answer.lower()
        for label in ('home', 'search', 'results', 'artist', 'playing', 'other'):
            if label in lowered:
                return label
    except Exception as e:
        log(f'   ⚠️ Vision model failed: {e}')

    return 'other'


def get_spotify_playback_snapshot():
    try:
        result = adb(['shell', 'dumpsys', 'media_session'], capture_output=True, timeout=10)
        lines = result.stdout.splitlines()

        for index, line in enumerate(lines):
            if SPOTIFY_PACKAGE not in line:
                continue

            window = '\n'.join(lines[index:index + 80])
            state_match = re.search(r'state=PlaybackState \{state=(\d+)', window)
            position_match = re.search(r'position=(\d+)', window)
            title_match = re.search(r'description=([^,\n]+)', window)

            return {
                'playing': state_match is not None and state_match.group(1) == '3',
                'position': int(position_match.group(1)) if position_match else None,
                'title': title_match.group(1).strip() if title_match else None,
            }
    except Exception as e:
        log(f'   ⚠️ Could not get playback snapshot: {e}')

    return {
        'playing': False,
        'position': None,
        'title': None,
    }


def confirm_playback_started():
    first = get_spotify_playback_snapshot()
    if not first['playing']:
        return False

    time.sleep(3)
    second = get_spotify_playback_snapshot()

    if not second['playing']:
        return False

    if first['position'] is not None and second['position'] is not None:
        return second['position'] > first['position']

    return second['title'] is not None


def step_go_home():
    log('━━━ STEP 1: Reset Spotify ━━━')
    tap_bottom_nav('home')
    time.sleep(2)


def step_go_to_search():
    log('━━━ STEP 2: Open Search ━━━')
    
    # Try multiple attempts to get to search screen
    for attempt in range(3):
        if tap_bottom_nav('search'):
            time.sleep(2)
            
            # Try multiple detection attempts
            for detect_attempt in range(3):
                current_screen = identify_screen(capture_screen())
                if current_screen in {'search', 'results'}:
                    log(f'   ✅ Confirmed search screen (attempt {detect_attempt+1})')
                    return True
                time.sleep(1)
            
            log(f'   Attempt {attempt+1}: Got {current_screen}, retrying...')
            
            # Recovery: force close and reopen if still failing
            if attempt < 2:
                log('   🔄 Force closing Spotify and retrying...')
                adb(['shell', 'am', 'force-stop', SPOTIFY_PACKAGE], timeout=10)
                time.sleep(2)
                open_spotify()
                time.sleep(3)
    
    log('❌ Could not confirm Search screen after 3 attempts')
    return False


def step_search_artist():
    log(f'━━━ STEP 3: Search {ARTIST_NAME} ━━━')
    x, y = find_search_field_coords()
    tap(x, y, 'Search field')
    time.sleep(0.8)

    clear_search_query_if_needed()

    type_text(ARTIST_NAME)
    press_enter()
    time.sleep(3)

    current_screen = identify_screen(capture_screen())
    log(f'   📱 Detected screen after search: {current_screen}')
    return current_screen in ('results', 'artist')


def step_open_artist():
    log(f"━━━ STEP 4: Open Artist '{ARTIST_NAME}' ━━━")
    x, y = find_artist_row_coords()
    tap(x, y, f'Artist row: {ARTIST_NAME}')
    time.sleep(3)

    current_screen = identify_screen(capture_screen())
    log(f'   📱 Detected screen after artist tap: {current_screen}')
    return current_screen == 'artist'


def step_follow_artist():
    log('━━━ STEP 5: Follow Artist ━━━')
    image_path = capture_screen()
    x, y = locate_element(image_path, 'the Follow button on the artist page', COORDS['artist_follow'])
    tap(x, y, 'Follow')
    human_pause(2, 3)


def step_stream_songs():
    log('━━━ STEP 6: Stream Songs ━━━')
    streams = 0

    for index, fallback in enumerate(COORDS['song_rows'], start=1):
        image_path = capture_screen()
        x, y = locate_element(
            image_path,
            f'the row for song number {index} in the Popular list on the artist page',
            fallback,
        )
        tap(x, y, f'Song {index}')

        if not confirm_playback_started():
            log('   ⚠️ Playback not confirmed, going back to artist page')
            press_back()
            time.sleep(2)
            continue

        log(f'   ▶️ Streaming for {STREAM_SECONDS}s...')
        time.sleep(STREAM_SECONDS + random.randint(0, 5))
        streams += 1
        log(f'   ✅ Stream {streams} counted')
        press_back()
        time.sleep(2)

        screen = identify_screen(capture_screen())
        if screen != 'artist':
            log(f'   ↩️ Returned to {screen}, trying to recover artist page')
            press_back()
            time.sleep(2)

        human_pause(2, 4)

    return streams


def run():
    log('=' * 58)
    log('🎵 Spotify Bot — Moondream Vision')
    log(f'🎤 Artist: {ARTIST_NAME}')
    log(f'🤖 Model: {MODEL_NAME}')
    log(f'🎯 Target: {STREAMS_TARGET} streams')
    log(f'⏱️ Per song: {STREAM_SECONDS}s')
    log('=' * 58)

    # Check ADB connection
    if not device_is_connected():
        log('❌ No ADB device detected. Connect the phone and authorize USB debugging.')
        return
    
    # Check Ollama health
    if not check_ollama_health():
        log('❌ Ollama not ready. Please start Ollama and load the model.')
        log(f'   Run: ollama serve')
        log(f'   Then: ollama pull {MODEL_NAME}')
        return

    log('Starting in 5 seconds...')
    time.sleep(5)

    total_streams = 0
    rounds = 0

    while total_streams < STREAMS_TARGET:
        rounds += 1
        log(f'\n🔄 ROUND {rounds} | ✅ {total_streams}/{STREAMS_TARGET}\n')

        try:
            open_spotify()
            human_pause(2, 3)
            step_go_home()

            if not step_go_to_search():
                log('❌ Could not confirm Search screen. Retrying round.')
                continue

            if not step_search_artist():
                log('❌ Could not confirm search results. Retrying round.')
                continue

            if not step_open_artist():
                log('❌ Could not confirm artist page. Retrying round.')
                continue

            if rounds == 1:
                step_follow_artist()

            streams = step_stream_songs()
            total_streams += streams
            log(f'\n📊 Round {rounds}: {streams} streams | Total: {total_streams}')

            if total_streams < STREAMS_TARGET:
                pause_seconds = random.randint(20, 45)
                log(f'😴 Break: {pause_seconds}s...')
                time.sleep(pause_seconds)
                
        except KeyboardInterrupt:
            log('\n⚠️ Bot interrupted by user')
            break
        except Exception as e:
            log(f'❌ Error in round {rounds}: {e}')
            log('Waiting 10 seconds before retry...')
            time.sleep(10)
            continue

    log('')
    log('=' * 58)
    log(f'✅ DONE! {total_streams} streams for {ARTIST_NAME}')
    log('=' * 58)


if __name__ == '__main__':
    run()