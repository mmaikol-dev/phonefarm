import datetime
import random
import re
import subprocess
import time
import xml.etree.ElementTree as ET


SPOTIFY_PACKAGE = 'com.spotify.music'
SPOTIFY_ACTIVITY = 'com.spotify.music/.MainActivity'
ARTIST_NAME = 'Wakadinali'
STREAMS_TARGET = 10
STREAM_SECONDS = 35
LOG_FILE = 'spotify_log.txt'
UI_WAIT_SECONDS = 10
UI_POLL_SECONDS = 0.8

# Coordinates for 1080x2400 resolution – used as fallbacks
COORDS = {
    'home_tab': (100, 2328),
    'search_tab': (324, 2288),
    'search_field': (350, 124),
    'artist_result': (228, 263),
    'artist_follow': (884, 261),
    'artist_play_button': (540, 480),
    'song_rows': [
        (232, 655),
        (229, 807),
        (227, 951),
        (226, 1101),
        (226, 1254),
    ],
}

# Alternative coordinates for different Spotify versions
FALLBACK_COORDS = {
    'home_tab': [(100, 2288), (140, 2288), (120, 2235)],
    'search_tab': [(324, 2328), (300, 2288), (360, 2288), (324, 2235)],
    'search_field': [(540, 200), (350, 180), (350, 124)],
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
        raise


def tap(x, y, label=''):
    if label:
        log(f'   👆 Tap: {label} ({x},{y})')
    adb(['shell', 'input', 'tap', str(x), str(y)])
    time.sleep(random.uniform(0.8, 1.2))


def type_text(text):
    """Type text using ADB input text command."""
    log(f'   ⌨️ Typing: "{text}"')
    safe_text = text.replace(' ', '%s').replace('&', '\\&').replace(';', '\\;')
    adb(['shell', 'input', 'text', safe_text])
    time.sleep(1.0)


def type_char_by_char(text):
    """Type text character by character (more reliable for some devices)."""
    log(f'   ⌨️ Typing (char by char): "{text}"')
    for char in text:
        if char == ' ':
            adb(['shell', 'input', 'keyevent', 'KEYCODE_SPACE'])
        else:
            adb(['shell', 'input', 'text', char])
        time.sleep(0.1)
    time.sleep(0.5)


def press_enter():
    """Press the Enter/Return key."""
    log('   ⌨️ Pressing Enter')
    adb(['shell', 'input', 'keyevent', 'KEYCODE_ENTER'])
    time.sleep(1.5)


def press_back():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_BACK'])
    time.sleep(1.0)


def press_home():
    adb(['shell', 'input', 'keyevent', 'KEYCODE_HOME'])
    time.sleep(1.0)


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


def human_pause(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))


def device_is_connected():
    try:
        result = adb(['devices'], capture_output=True, timeout=10)
        return any('\tdevice' in line for line in result.stdout.splitlines())
    except Exception:
        return False


def open_spotify():
    log('📱 Opening Spotify...')
    wake_and_unlock_device()
    adb(['shell', 'am', 'start', '-n', SPOTIFY_ACTIVITY])
    time.sleep(4)


def get_foreground_package():
    try:
        result = adb(['shell', 'dumpsys', 'window'], capture_output=True, timeout=10)
        if result.returncode != 0:
            return ''

        for line in result.stdout.splitlines():
            if 'mCurrentFocus' in line or 'mFocusedApp' in line:
                match = re.search(r' ([A-Za-z0-9._]+)/', line)
                if match:
                    return match.group(1)
    except Exception:
        pass

    return ''


def ensure_spotify_foreground():
    package_name = get_foreground_package()
    if package_name != SPOTIFY_PACKAGE:
        log(f'   Spotify not foreground ({package_name or "unknown"}) — reopening')
        open_spotify()
        time.sleep(2)


def parse_bounds(bounds):
    match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds or '')
    if not match:
        return None
    return tuple(map(int, match.groups()))


def bounds_center(bounds):
    parsed = parse_bounds(bounds)
    if not parsed:
        return None, None
    x1, y1, x2, y2 = parsed
    return (x1 + x2) // 2, (y1 + y2) // 2


def dump_ui():
    """Dump UI hierarchy with retry logic."""
    remote_path = '/sdcard/window_dump.xml'
    
    for attempt in range(3):
        try:
            adb(['shell', 'rm', remote_path], capture_output=True, timeout=5)
            adb(['shell', 'uiautomator', 'dump', remote_path], capture_output=True, timeout=15)
            time.sleep(0.8)
            
            file_check = adb(['shell', 'test', '-f', remote_path, '&&', 'echo', 'exists'], capture_output=True, timeout=5)
            if 'exists' not in file_check.stdout:
                time.sleep(0.5)
                continue
            
            read_result = adb(['exec-out', 'cat', remote_path], capture_output=True, timeout=10)
            if not read_result.stdout or len(read_result.stdout) < 100:
                time.sleep(0.5)
                continue
            
            xml_start = read_result.stdout.find('<?xml')
            if xml_start == -1:
                time.sleep(0.5)
                continue
            
            return ET.fromstring(read_result.stdout[xml_start:])
            
        except ET.ParseError:
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    
    return None


def iter_nodes(root):
    if root is None:
        return []
    return list(root.iter('node'))


def node_resource_id(node):
    return node.attrib.get('resource-id', '')


def node_text(node):
    return node.attrib.get('text', '').strip()


def node_desc(node):
    return node.attrib.get('content-desc', '').strip()


def node_attrib(node, attr):
    return node.attrib.get(attr, '')


def node_center(node):
    return bounds_center(node.attrib.get('bounds'))


def node_clickable(node):
    return node_attrib(node, 'clickable') == 'true'


def find_first_node(root, predicate):
    if root is None:
        return None
    for node in iter_nodes(root):
        if predicate(node):
            return node
    return None


def wait_for(description, predicate, timeout=UI_WAIT_SECONDS, poll=UI_POLL_SECONDS):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if predicate():
                log(f'   ✅ {description}')
                return True
        except Exception:
            pass
        time.sleep(poll)

    log(f'   ❌ Timed out waiting for {description}')
    return False


def find_node_by_resource_id(resource_id):
    root = dump_ui()
    if root is None:
        return None
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
    return (
        has_resource_id('com.spotify.music:id/search_root') or
        has_resource_id('com.spotify.music:id/search_field_root') or
        has_resource_id('com.spotify.music:id/query') or
        screen_contains_text('what do you want to listen to?', 'discover something new', 'browse all')
    )


def is_search_results_screen():
    """Check if current screen shows search results."""
    return (
        has_resource_id('com.spotify.music:id/search_content_recyclerview') or
        screen_contains_text(ARTIST_NAME, 'playlists', 'artists', 'songs', 'albums')
    )


def is_artist_screen():
    """Check if current screen is an artist page."""
    root = dump_ui()
    if root is None:
        return False
    
    artist_name = ARTIST_NAME.lower()
    
    return (
        has_resource_id('com.spotify.music:id/follow_button') or
        screen_contains_text(ARTIST_NAME, 'monthly listeners', 'popular', 'follow') or
        find_first_node(
            root,
            lambda item: artist_name in node_text(item).lower() and 
                        ('artist' in node_desc(item).lower() or 'follow' in node_text(item).lower())
        ) is not None
    )


def is_keyboard_visible():
    """Check if keyboard is visible."""
    result = adb(['shell', 'dumpsys', 'input_method'], capture_output=True, timeout=5)
    return 'mInputShown=true' in result.stdout


def get_spotify_playback_snapshot():
    """Get current Spotify playback state."""
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
            
            is_playing = state_match is not None and state_match.group(1) == '3'
            
            return {
                'playing': is_playing,
                'position': int(position_match.group(1)) if position_match else None,
                'title': title_match.group(1).strip() if title_match else None,
            }
    except Exception:
        pass

    return {
        'playing': False,
        'position': None,
        'title': None,
    }


def confirm_playback_started():
    """Confirm that playback actually started."""
    time.sleep(2)
    
    first = get_spotify_playback_snapshot()
    if not first['playing']:
        return False

    time.sleep(3)
    second = get_spotify_playback_snapshot()
    
    if not second['playing']:
        return False

    if first['position'] is not None and second['position'] is not None:
        return second['position'] > first['position']
    
    return second['playing']


def find_search_tab_coords():
    """Find search tab coordinates using UI hierarchy."""
    root = dump_ui()
    if root is not None:
        node = find_first_node(
            root,
            lambda item: (
                'search, tab' in node_desc(item).lower() or
                'search tab' in node_desc(item).lower() or
                (
                    node_clickable(item) and
                    node_text(item).strip().lower() == 'search' and
                    (node_center(item)[1] or 0) > 2000
                )
            ),
        )
        
        if node is not None:
            x, y = node_center(node)
            if x is not None and y is not None:
                return x, y
    
    return COORDS['search_tab']


def find_search_field_coords():
    """Find search field coordinates by looking for the placeholder text."""
    root = dump_ui()
    if root is None:
        return COORDS['search_field']
    
    # Look for element with the placeholder text "what do you want to listen to?"
    placeholder = "what do you want to listen to?"
    node = find_first_node(
        root,
        lambda item: (
            placeholder in node_text(item).lower() or
            placeholder in node_desc(item).lower()
        )
    )
    if node is not None:
        x, y = node_center(node)
        if x is not None and y is not None:
            log(f'   Found search field via placeholder text at ({x},{y})')
            return x, y
    
    # Next, look for specific resource IDs of the search input
    for rid in ('com.spotify.music:id/query', 'com.spotify.music:id/search_field_root'):
        node = find_node_by_resource_id(rid)
        if node is not None:
            x, y = node_center(node)
            if x is not None and y is not None:
                log(f'   Found search field via resource-id {rid} at ({x},{y})')
                return x, y
    
    # Fallback: look for a clickable node with "search" in text/desc, but not the header
    node = find_first_node(
        root,
        lambda item: (
            node_clickable(item) and
            ('search' in node_text(item).lower() or 'search' in node_desc(item).lower())
        ) and node_resource_id(item) != 'com.spotify.music:id/faceheader_title'
    )
    if node is not None:
        x, y = node_center(node)
        if x is not None and y is not None:
            log(f'   Found search field via text/desc at ({x},{y})')
            return x, y
    
    # Also try looking for a clickable node near the top of the screen (y < 400)
    for node in iter_nodes(root):
        if node_clickable(node):
            x, y = node_center(node)
            if x is not None and y is not None and y < 400:
                log(f'   Found candidate near top at ({x},{y})')
                return x, y
    
    return COORDS['search_field']


def focus_search_field():
    """Tap the search field to focus it."""
    log('   🔍 Focusing search field')
    
    # Primary: try the known working coordinate
    known_x, known_y = COORDS['search_field']
    log(f'   Trying known coordinate ({known_x}, {known_y})')
    tap(known_x, known_y, 'Known search field')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    
    # Secondary: try to find the search field via UI
    log('   Known coordinate failed, trying UI detection')
    x, y = find_search_field_coords()
    log(f'   UI detected search field at ({x}, {y})')
    tap(x, y, 'UI-detected search field')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    
    # Fallback: try alternative coordinates from list
    log('   Still no keyboard, trying fallback coordinates')
    for alt_x, alt_y in FALLBACK_COORDS['search_field']:
        tap(alt_x, alt_y, f'Fallback ({alt_x},{alt_y})')
        time.sleep(2)
        if is_keyboard_visible():
            log('   ✅ Keyboard is now visible')
            return True
    
    # Last resort: tap center of screen
    log('   Trying center screen tap')
    tap(540, 500, 'Center screen')
    time.sleep(2)
    if is_keyboard_visible():
        log('   ✅ Keyboard is visible')
        return True
    
    log('   ❌ Could not focus search field')
    return False


def clear_search_query():
    """Clear existing search query."""
    log('   🧹 Clearing search field')
    
    # If keyboard is not visible, we cannot send key events
    if not is_keyboard_visible():
        log('   Keyboard not visible, cannot clear')
        return False
    
    # Select all text
    adb(['shell', 'input', 'keyevent', 'KEYCODE_MOVE_END'])
    time.sleep(0.2)
    adb(['shell', 'input', 'keyevent', 'KEYCODE_SHIFT_LEFT', '--longpress'])
    time.sleep(0.3)
    
    # Delete
    adb(['shell', 'input', 'keyevent', 'KEYCODE_DEL'])
    time.sleep(0.5)
    return True


def get_search_field_text():
    """Get the current text from the search field."""
    root = dump_ui()
    if root is None:
        return ''
    
    # Look for element that is focused (has focus="true") - that should be the active input
    focused_node = find_first_node(root, lambda item: node_attrib(item, 'focused') == 'true')
    if focused_node is not None:
        return node_text(focused_node)
    
    # Alternatively, look for an editable text field (class="android.widget.EditText")
    edit_text_node = find_first_node(
        root,
        lambda item: node_attrib(item, 'class') == 'android.widget.EditText'
    )
    if edit_text_node is not None:
        return node_text(edit_text_node)
    
    # Fallback to placeholder detection
    placeholder = "what do you want to listen to?"
    node = find_first_node(
        root,
        lambda item: (
            placeholder in node_text(item).lower() or
            placeholder in node_desc(item).lower() or
            node_resource_id(item) in ('com.spotify.music:id/query', 'com.spotify.music:id/search_field_root')
        )
    )
    if node is not None:
        return node_text(node)
    return ''


def ensure_search_field_ready():
    """Focus search field, clear it, and type artist name. Returns True if successful."""
    log('   🔍 Ensuring search field is ready')
    
    # First, try to focus the field
    if not is_keyboard_visible():
        if not focus_search_field():
            return False
    else:
        log('   Keyboard already visible')
    
    # Clear existing text
    clear_search_query()
    time.sleep(0.5)
    
    # Type the artist name using standard method
    type_text(ARTIST_NAME)
    time.sleep(1)  # Wait a bit for UI to update
    
    # Verify that the text actually appears
    entered_text = get_search_field_text()
    if ARTIST_NAME.lower() in entered_text.lower():
        log(f'   ✅ Verified text in search field: "{entered_text}"')
        return True
    else:
        log(f'   ⚠️ Text verification failed. Found: "{entered_text}"')
        # Try character-by-character typing as fallback
        log('   Trying character-by-character typing...')
        # Clear again
        clear_search_query()
        time.sleep(0.5)
        type_char_by_char(ARTIST_NAME)
        time.sleep(1)
        entered_text = get_search_field_text()
        if ARTIST_NAME.lower() in entered_text.lower():
            log(f'   ✅ Verified text after char-by-char: "{entered_text}"')
            return True
        else:
            log(f'   ❌ Still no text. Found: "{entered_text}"')
            return False


def find_artist_row_coords():
    """Find artist row coordinates in search results."""
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
            if x is not None and y is not None:
                return max(120, x - 220), y

    return COORDS['artist_result']


def find_follow_button_coords():
    """Find follow button coordinates."""
    node = find_node_by_resource_id('com.spotify.music:id/follow_button')
    if node is not None:
        x, y = node_center(node)
        if x is not None and y is not None:
            return x, y
    return COORDS['artist_follow']


def find_song_rows():
    """Find all song rows in the artist's popular list."""
    root = dump_ui()
    if root is None:
        return []
    
    rows = []
    for node in iter_nodes(root):
        # Look for nodes that likely represent a song row
        # Typically these have children with resource-ids "title" and "subtitle"
        title_node = None
        subtitle_node = None
        
        for child in node.iter('node'):
            rid = node_resource_id(child)
            if rid == 'com.spotify.music:id/title':
                title_node = child
            elif rid == 'com.spotify.music:id/subtitle':
                subtitle_node = child
        
        if title_node is None or subtitle_node is None:
            continue
        
        title = node_text(title_node)
        subtitle = node_text(subtitle_node).lower()
        
        # Skip if it's clearly not a song (e.g., playlist, album, podcast)
        if any(skip in subtitle for skip in ['playlist', 'album', 'podcast', 'episode', 'video']):
            continue
        
        # If it has a duration like "3:45" or contains "song"/"track", likely a song
        if 'song' in subtitle or 'track' in subtitle or re.search(r'\d+:\d+', subtitle):
            x, y = node_center(node)
            if x is not None and y is not None:
                # Try to tap on the left side where the title is
                bounds = parse_bounds(node.attrib.get('bounds', ''))
                if bounds:
                    x1, _, x2, _ = bounds
                    # Tap at one quarter from left (where title usually is)
                    tap_x = x1 + (x2 - x1) // 4
                else:
                    tap_x = x - 180  # fallback
                rows.append((y, (tap_x, y), title))
    
    # Sort by Y coordinate (top to bottom)
    rows.sort(key=lambda item: item[0])
    
    # Remove duplicates by title (some rows might appear twice due to hierarchy)
    seen = set()
    unique_rows = []
    for _, coords, title in rows:
        if title not in seen:
            seen.add(title)
            unique_rows.append((coords, title))
    
    return unique_rows


def step_go_home():
    """Navigate to Spotify home screen."""
    log('━━━ STEP 1: Reset to Home ━━━')
    ensure_spotify_foreground()
    
    for coords in [COORDS['home_tab']] + FALLBACK_COORDS['home_tab']:
        tap(coords[0], coords[1], 'Home tab')
        time.sleep(2)
        if screen_contains_text('jump back in', 'fresh new music', 'liked songs'):
            return True
    
    return False


def step_go_to_search():
    """Navigate to search screen."""
    log('━━━ STEP 2: Open Search ━━━')

    search_coords = [find_search_tab_coords()] + FALLBACK_COORDS['search_tab']
    
    for attempt, (x, y) in enumerate(search_coords[:5], 1):
        tap(x, y, f'Search tab (attempt {attempt})')
        
        if wait_for('Search screen', is_search_screen, timeout=5):
            return True

    return False


def step_search_artist():
    """Search for the target artist."""
    log(f'━━━ STEP 3: Search {ARTIST_NAME} ━━━')
    
    # Prepare search field (focus, clear, type)
    if not ensure_search_field_ready():
        log('   ❌ Could not prepare search field')
        return False
    
    # Press Enter to search
    press_enter()
    
    # Wait for search results
    return wait_for('Search results', is_search_results_screen, timeout=8)


def step_open_artist():
    """Open the artist page."""
    log(f"━━━ STEP 4: Open Artist '{ARTIST_NAME}' ━━━")
    
    x, y = find_artist_row_coords()
    tap(x, y, f'Artist: {ARTIST_NAME}')
    
    return wait_for('Artist page', is_artist_screen, timeout=8)


def step_follow_artist():
    """Follow the artist (only once)."""
    log('━━━ STEP 5: Follow Artist ━━━')
    
    x, y = find_follow_button_coords()
    if x is not None and y is not None:
        tap(x, y, 'Follow')
        human_pause(2, 3)
    else:
        log('   ℹ️ Follow button not found, already following?')


def step_stream_songs():
    """Stream songs from the artist's popular list."""
    log('━━━ STEP 6: Stream Songs ━━━')
    streams = 0
    
    # Scroll to make sure the Popular songs section is visible
    log('   📜 Scrolling to songs...')
    adb(['shell', 'input', 'swipe', '540', '1200', '540', '400', '300'])
    time.sleep(1.5)
    
    # Get dynamic song rows
    song_rows = find_song_rows()
    if not song_rows:
        log('   ⚠️ No song rows found dynamically, using fallback')
        song_rows = [(coords, f'Song {i+1}') for i, coords in enumerate(COORDS['song_rows'])]
    
    log(f'   Found {len(song_rows)} songs to stream')
    
    for index, (coords, title) in enumerate(song_rows[:5], 1):
        if streams >= STREAMS_TARGET:
            break
        
        x, y = coords
        log(f'\n   🎵 Song {index}: {title}')
        log(f'   👆 Tapping song row at ({x}, {y})')
        tap(x, y, title)
        
        # Wait for playback to start
        if not wait_for('Playback to start', confirm_playback_started, timeout=12, poll=1.5):
            log(f'   ⚠️ Playback not confirmed, skipping')
            press_back()
            time.sleep(2)
            continue
        
        log(f'   ▶️ Streaming for {STREAM_SECONDS}s...')
        time.sleep(STREAM_SECONDS + random.randint(0, 3))
        streams += 1
        log(f'   ✅ Stream {streams} counted')
        
        # Go back to artist page
        press_back()
        time.sleep(2)
        
        # Verify we're back on artist page
        if not is_artist_screen():
            log('   ↩️ Lost artist page, pressing back again')
            press_back()
            time.sleep(2)
        
        human_pause(2, 4)
    
    return streams


def run():
    """Main execution function."""
    log('=' * 55)
    log('🎵 Spotify Bot — UI Automator Control')
    log(f'🎤 Artist: {ARTIST_NAME}')
    log(f'🎯 Target: {STREAMS_TARGET} streams')
    log(f'⏱️ Per song: {STREAM_SECONDS}s')
    log('=' * 55)

    if not device_is_connected():
        log('❌ No ADB device detected.')
        return

    log('✅ ADB device detected')
    log('Starting in 5 seconds...')
    time.sleep(5)

    total_streams = 0
    rounds = 0
    followed = False

    while total_streams < STREAMS_TARGET:
        rounds += 1
        log(f'\n🔄 ROUND {rounds} | ✅ {total_streams}/{STREAMS_TARGET}\n')

        try:
            open_spotify()
            human_pause(2, 3)
            
            if not step_go_home():
                log('⚠️ Could not verify home screen')
            
            if not step_go_to_search():
                log('❌ Could not open Search. Retrying round.')
                continue
            
            if not step_search_artist():
                log('❌ Search results did not load. Retrying round.')
                continue
            
            if not step_open_artist():
                log('❌ Artist page did not open. Retrying round.')
                continue
            
            if not followed:
                step_follow_artist()
                followed = True
            
            streams = step_stream_songs()
            total_streams += streams
            log(f'\n📊 Round {rounds}: +{streams} streams | Total: {total_streams}/{STREAMS_TARGET}')
            
            if total_streams < STREAMS_TARGET:
                pause_seconds = random.randint(20, 45)
                log(f'😴 Break: {pause_seconds}s...')
                time.sleep(pause_seconds)
                
        except KeyboardInterrupt:
            log('\n⚠️ Bot interrupted by user')
            break
        except Exception as e:
            log(f'❌ Error in round {rounds}: {e}')
            import traceback
            traceback.print_exc()
            time.sleep(15)

    log('')
    log('=' * 55)
    log(f'✅ DONE! {total_streams}/{STREAMS_TARGET} streams for {ARTIST_NAME}')
    log('=' * 55)


if __name__ == '__main__':
    run()