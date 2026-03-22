import warnings
warnings.filterwarnings('ignore')

import google.generativeai as genai
from PIL import Image
import subprocess
import time
import random
import datetime
import re
import xml.etree.ElementTree as ET

# ── CONFIG ────────────────────────────────────────
API_KEY        = "AIzaSyCfyU_Ifv9W-Y5K9EzS7ZKBYZ-xb-ewgFw"
ARTIST_NAME    = "Wakadinali"
STREAMS_TARGET = 10
STREAM_SECONDS = 35
LOG_FILE       = "spotify_log.txt"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

# ── VERIFIED COORDINATES (1080x2400, density 440) ─
COORDS = {
    'home_tab':      (108, 2288),
    'search_tab':    (324, 2288),
    'library_tab':   (540, 2288),
    'mini_player':   (540, 2169),
    'mini_play':     (981, 2169),
    'back_button':   (71,  111),
}

# ── LOGGING ───────────────────────────────────────
def log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full = f"[{timestamp}] {message}"
    print(full)
    with open(LOG_FILE, 'a') as f:
        f.write(full + '\n')

# ── PHONE ACTIONS ─────────────────────────────────
def capture():
    subprocess.run(
        'adb exec-out screencap -p > screen.png',
        shell=True
    )
    time.sleep(0.5)
    return Image.open('screen.png')

def tap(x, y, label=""):
    if label:
        log(f"   👆 Tap: {label} ({x},{y})")
    subprocess.run([
        'adb', 'shell', 'input', 'tap', str(x), str(y)
    ])
    time.sleep(random.uniform(1.2, 2.0))

def type_text(text):
    log(f"   ⌨️  Type: {text}")
    safe = text.replace(' ', '%s')
    subprocess.run([
        'adb', 'shell', 'input', 'text', safe
    ])
    time.sleep(1.5)

def press_enter():
    subprocess.run([
        'adb', 'shell', 'input', 'keyevent', 'KEYCODE_ENTER'
    ])
    time.sleep(2.0)

def press_back():
    subprocess.run([
        'adb', 'shell', 'input', 'keyevent', 'KEYCODE_BACK'
    ])
    time.sleep(1.5)

def swipe_up():
    subprocess.run([
        'adb', 'shell', 'input', 'swipe',
        '540', '1400', '540', '600', '500'
    ])
    time.sleep(1.5)

def human_pause(min_s=1, max_s=3):
    time.sleep(random.uniform(min_s, max_s))

def open_spotify():
    log("📱 Opening Spotify...")
    subprocess.run([
        'adb', 'shell', 'am', 'start',
        '-n', 'com.spotify.music/.MainActivity'
    ])
    time.sleep(4)

def get_foreground_package():
    result = subprocess.run(
        ['adb', 'shell', 'dumpsys', 'window'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return ""

    for line in result.stdout.splitlines():
        if 'mCurrentFocus' in line or 'mFocusedApp' in line:
            match = re.search(r' ([A-Za-z0-9._]+)/', line)
            if match:
                return match.group(1)
    return ""

# ── GEMINI ────────────────────────────────────────
gemini_call_count = 0

def ask(image, question):
    global gemini_call_count
    gemini_call_count += 1

    # Rate limit — max 5 calls per minute on free tier
    # Wait 15 seconds between calls to be safe
    time.sleep(15)

    try:
        log(f"   🧠 Gemini call #{gemini_call_count}...")
        response = model.generate_content([question, image])
        answer = response.text.strip()
        log(f"   💬 Answer: {answer[:120]}")
        return answer
    except Exception as e:
        if '429' in str(e):
            log("   ⏳ Rate limit — waiting 60s...")
            time.sleep(60)
            return ask(image, question)
        log(f"   ⚠️  Error: {e}")
        return ""

def parse_bounds(bounds):
    match = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not match:
        return None
    x1, y1, x2, y2 = map(int, match.groups())
    return x1, y1, x2, y2

def bounds_center(bounds):
    parsed = parse_bounds(bounds)
    if not parsed:
        return None, None
    x1, y1, x2, y2 = parsed
    return (x1 + x2) // 2, (y1 + y2) // 2

def dump_ui():
    result = subprocess.run(
        ['adb', 'exec-out', 'uiautomator', 'dump', '/dev/tty'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    xml_start = result.stdout.find('<?xml')
    if xml_start == -1:
        return None
    try:
        return ET.fromstring(result.stdout[xml_start:])
    except ET.ParseError:
        return None

def find_first_node(root, predicate):
    if root is None:
        return None
    for node in root.iter('node'):
        if predicate(node):
            return node
    return None

def iter_nodes(root):
    if root is None:
        return []
    return list(root.iter('node'))

def child_nodes(node):
    return list(node)

def textish(node):
    values = [
        node.attrib.get('text', ''),
        node.attrib.get('content-desc', ''),
        node.attrib.get('resource-id', '')
    ]
    return " ".join(v for v in values if v).lower()

def find_ui_coords(*terms):
    root = dump_ui()
    lowered_terms = [term.lower() for term in terms]

    node = find_first_node(
        root,
        lambda item: all(term in textish(item) for term in lowered_terms)
    )
    if not node:
        return None, None

    return bounds_center(node.attrib.get('bounds'))

def node_package(node):
    return node.attrib.get('package', '')

def node_clickable(node):
    return node.attrib.get('clickable') == 'true'

def node_bounds(node):
    return parse_bounds(node.attrib.get('bounds'))

def node_center(node):
    return bounds_center(node.attrib.get('bounds'))

def center_left_of_node(node):
    parsed = node_bounds(node)
    if not parsed:
        return None, None
    x1, y1, x2, y2 = parsed
    safe_x = x1 + max(40, (x2 - x1) // 4)
    safe_y = (y1 + y2) // 2
    return safe_x, safe_y

def node_resource_id(node):
    return node.attrib.get('resource-id', '')

def node_text(node):
    return node.attrib.get('text', '').strip()

def node_desc(node):
    return node.attrib.get('content-desc', '').strip()

def find_node_by_resource_id(resource_id):
    root = dump_ui()
    return find_first_node(
        root,
        lambda item: node_resource_id(item) == resource_id
    )

def node_has_desc_prefix(node, prefix):
    return node_desc(node).lower().startswith(prefix.lower())

def node_label_contains(node, text):
    lowered = text.lower()
    return lowered in node_text(node).lower() or lowered in node_desc(node).lower()

def find_row_root_by_title(title_text, subtitle_text=None):
    root = dump_ui()
    title_lower = title_text.lower()
    subtitle_lower = subtitle_text.lower() if subtitle_text else None

    for node in iter_nodes(root):
        if node_resource_id(node) != 'com.spotify.music:id/row_root':
            continue

        found_title = False
        found_subtitle = subtitle_lower is None

        for child in node.iter('node'):
            resource_id = node_resource_id(child)
            text_value = node_text(child).lower()

            if resource_id == 'com.spotify.music:id/title' and title_lower in text_value:
                found_title = True
            if subtitle_lower and resource_id == 'com.spotify.music:id/subtitle' and subtitle_lower in text_value:
                found_subtitle = True

        if found_title and found_subtitle:
            return node

    return None

def find_search_results_rows():
    root = dump_ui()
    rows = []
    for node in iter_nodes(root):
        if node_resource_id(node) == 'com.spotify.music:id/row_root':
            rows.append(node)
    return rows

def find_search_tab_coords():
    root = dump_ui()
    node = find_first_node(
        root,
        lambda item: node_clickable(item) and node_has_desc_prefix(item, 'Search, Tab')
    )
    if not node:
        return None, None
    return node_center(node)

def find_search_field_coords():
    for resource_id in (
        'com.spotify.music:id/query',
        'com.spotify.music:id/search_field_root',
    ):
        node = find_node_by_resource_id(resource_id)
        if node:
            return node_center(node)

    root = dump_ui()
    node = find_first_node(
        root,
        lambda item: node_clickable(item) and (
            node_label_contains(item, 'what do you want to listen to')
            or node_label_contains(item, 'search')
        ) and node_center(item)[1] < 400
    )
    if node:
        return node_center(node)
    return None, None

def find_artist_result_coords(artist_name):
    node = find_row_root_by_title(artist_name, 'artist')
    if not node:
        return None, None
    return center_left_of_node(node)

def find_follow_button_coords():
    for node in find_search_results_rows():
        found_artist = False
        follow_button = None

        for child in node.iter('node'):
            resource_id = node_resource_id(child)
            if resource_id == 'com.spotify.music:id/subtitle' and 'artist' in node_text(child).lower():
                found_artist = True
            if resource_id == 'com.spotify.music:id/follow_button':
                follow_button = child

        if found_artist and follow_button:
            return node_center(follow_button)

    node = find_node_by_resource_id('com.spotify.music:id/follow_button')
    if node:
        return node_center(node)
    return None, None

def find_song_row_coords_from_ui():
    rows = []

    for node in find_search_results_rows():
        title_node = None
        subtitle_node = None

        for child in node.iter('node'):
            resource_id = node_resource_id(child)
            if resource_id == 'com.spotify.music:id/title':
                title_node = child
            elif resource_id == 'com.spotify.music:id/subtitle':
                subtitle_node = child

        if not title_node or not subtitle_node:
            continue

        subtitle_text = node_text(subtitle_node).lower()
        if 'song' not in subtitle_text:
            continue

        row_bounds = node_bounds(node)
        if not row_bounds:
            continue

        _, y1, _, _ = row_bounds
        rows.append((y1, center_left_of_node(node), node_text(title_node)))

    rows.sort(key=lambda item: item[0])
    return [coords for _, coords, _ in rows]

def extract_xy(answer):
    pair_match = re.search(r'(\d{1,4})\s*,\s*(\d{1,4})', answer)
    if pair_match:
        x, y = map(int, pair_match.groups())
        if 0 < x < 1080 and 0 < y < 2400:
            return x, y

    numbers = re.findall(r'\d+', answer)
    if len(numbers) >= 2:
        x, y = map(int, numbers[-2:])
        if 0 < x < 1080 and 0 < y < 2400:
            return x, y

    return None, None

def find_element_coords(screen, description):
    """Ask Gemini to find element and return x,y"""
    answer = ask(screen, f"""
        This is an Android phone screenshot (1080x2400 pixels).
        Find this UI element: {description}

        Return ONLY the tap coordinates in format: X,Y
        Example: 212,1530

        Important:
        - Tap the main target itself, not a nearby menu, overflow, or play button.
        - Prefer the center-left area of list rows.
        If not found return: 0,0
    """)
    return extract_xy(answer)

def what_screen_is_this(screen):
    """Ask Gemini to identify current screen"""
    answer = ask(screen, """
        Look at this Spotify screenshot.
        What screen is this? Choose ONE:
        - home (showing playlists and recommendations)
        - search (showing search bar)
        - search_active (search bar with cursor, ready to type)
        - results (showing search results list)
        - artist (showing artist page with Follow button and songs)
        - playing (showing now playing screen)
        - other

        Answer with ONLY one word from the list above.
    """)
    # Extract just the screen name
    for screen_type in ['search_active', 'search', 'results', 'artist', 'playing', 'home']:
        if screen_type in answer.lower():
            return screen_type
    return 'other'

# ── STEPS ─────────────────────────────────────────

def step_go_home():
    log("━━━ Going Home ━━━")
    package_name = get_foreground_package()
    log(f"   Foreground package: {package_name or 'unknown'}")

    if package_name != 'com.spotify.music':
        log("   Spotify is not in the foreground — reopening app")
        open_spotify()

    # Tap home tab with correct coordinates
    tap(*COORDS['home_tab'], "Home tab")
    time.sleep(2)

def step_go_to_search():
    log("━━━ STEP 2: Open Search ━━━")

    x, y = find_search_tab_coords()
    if x and y:
        tap(x, y, "Search tab (UI dump)")
    else:
        tap(*COORDS['search_tab'], "Search tab (default)")
    time.sleep(2.5)

    # Check what screen we're on
    screen = capture()
    if find_search_field_coords() != (None, None):
        log("✅ Search field detected from UI dump")
        return True, screen

    current = what_screen_is_this(screen)
    log(f"   Current screen: {current}")

    if current in ('search', 'search_active'):
        log("✅ On search page!")
        return True, screen
    else:
        log(f"⚠️  Got '{current}' — asking Gemini to find search tab...")
        # Ask Gemini to find the actual search tab
        x, y = find_element_coords(screen,
            "The Search icon/tab in the bottom navigation bar of Spotify")
        if x and y:
            log(f"   Gemini found search tab at: {x},{y}")
            tap(x, y, "Search tab (Gemini found)")
            time.sleep(2.5)
            screen = capture()
            return True, screen
        else:
            log("❌ Could not find search tab")
            return False, screen

def step_activate_and_type():
    log("━━━ STEP 3: Search for Artist ━━━")

    screen = capture()
    search_field_x, search_field_y = find_search_field_coords()
    current = 'search_active' if search_field_x and search_field_y else what_screen_is_this(screen)

    if current != 'search_active':
        if search_field_x and search_field_y:
            log(f"   Search field found from UI dump at: {search_field_x},{search_field_y}")
            tap(search_field_x, search_field_y, "Search field (UI dump)")
        else:
            x, y = find_element_coords(screen,
                "The search input field/bar that says 'What do you want to listen to?' in Spotify")

            if x and y:
                log(f"   Search bar found at: {x},{y}")
                tap(x, y, "Search bar")
            else:
                log("   Using default search bar position")
                tap(360, 216, "Search bar (default)")

        time.sleep(1.5)

    # Type artist name
    type_text(ARTIST_NAME)
    time.sleep(1)
    press_enter()
    time.sleep(3)

    screen = capture()
    current = what_screen_is_this(screen)
    log(f"   After search: {current}")
    return screen

def step_tap_artist(screen):
    log(f"━━━ STEP 4: Tap Artist '{ARTIST_NAME}' ━━━")

    x, y = find_artist_result_coords(ARTIST_NAME)
    if x and y:
        log(f"   Artist found from UI dump at: {x},{y}")
        tap(x, y, f"Artist: {ARTIST_NAME} (UI dump)")
    else:
        # Ask Gemini to find the Artist result
        x, y = find_element_coords(screen, f"""
            The search result row showing '{ARTIST_NAME}'
            with the label 'Artist' underneath it.
            NOT a playlist or song.
            Tap the left-center of the artist row, not the image, not the menu.
        """)

        if x and y:
            log(f"   Artist found at: {x},{y}")
            tap(x, y, f"Artist: {ARTIST_NAME}")
        else:
            log("   Using default artist position")
            tap(360, 880, "Artist (default)")

    time.sleep(3)

    screen = capture()
    current = what_screen_is_this(screen)
    log(f"   After tap: {current}")

    return current == 'artist', screen

def step_follow_artist(screen):
    log("━━━ STEP 5: Follow Artist ━━━")

    x, y = find_follow_button_coords()
    if not (x and y):
        x, y = find_element_coords(screen,
            "The Follow button on this Spotify artist page")

    if x and y:
        log(f"   Follow button at: {x},{y}")
        tap(x, y, "Follow")
        log("✅ Followed!")
    else:
        log("ℹ️  Follow button not found (may already follow)")

def find_song_row_coords(screen, ordinal):
    song_coords = find_song_row_coords_from_ui()
    ordinal_index = {
        'first': 0,
        'second': 1,
        'third': 2,
        'fourth': 3,
        'fifth': 4,
    }
    index = ordinal_index.get(ordinal)
    if index is not None and index < len(song_coords):
        return song_coords[index]

    return find_element_coords(screen, f"""
        The {ordinal} visible song row in the Popular songs list on this Spotify artist page.
        Return coordinates for the song title area on the left side of the row.
        Do NOT tap the three-dot menu, overflow button, or any play/shuffle/follow controls.
    """)

def step_stream_songs(screen):
    log("━━━ STEP 6: Stream Songs ━━━")
    streams = 0

    ordinals = ['first', 'second', 'third', 'fourth', 'fifth']

    for i, ordinal in enumerate(ordinals, start=1):
        log(f"")
        refresh = capture()
        x, y = find_song_row_coords(refresh, ordinal)

        if not (x and y):
            fallback_y = 825 + ((i - 1) * 115)
            x, y = 360, fallback_y
            log(f"   Using fallback coords for song {i}: {x},{y}")
        else:
            log(f"   Song {i} at: {x},{y}")

        tap(x, y, f"Song {i}")
        time.sleep(3)

        # Quick check if playing
        screen = capture()
        answer = ask(screen, """
            Is there a song currently playing?
            Look for a mini player bar at the bottom.
            Answer ONLY: yes or no
        """)

        if 'yes' in answer.lower():
            log(f"   ▶️  Playing — waiting {STREAM_SECONDS}s...")
            time.sleep(STREAM_SECONDS + random.randint(0, 8))
            streams += 1
            log(f"   ✅ Stream {streams} counted!")
        else:
            log(f"   ⚠️  Not confirmed playing — waiting anyway")
            time.sleep(STREAM_SECONDS)
            streams += 1

        human_pause(2, 4)

    return streams

# ── MAIN ──────────────────────────────────────────
def run():
    log("=" * 55)
    log(f"🎵 Spotify Bot — Fully Dynamic")
    log(f"🎤 Artist:  {ARTIST_NAME}")
    log(f"🎯 Target:  {STREAMS_TARGET} streams")
    log(f"⏱️  Per song: {STREAM_SECONDS}s")
    log(f"🤖 Model: gemini-3-flash-preview")
    log("=" * 55)
    log("Starting in 5 seconds...")
    time.sleep(5)

    total_streams = 0
    rounds = 0

    while total_streams < STREAMS_TARGET:
        rounds += 1
        log(f"\n🔄 ROUND {rounds} | ✅ {total_streams}/{STREAMS_TARGET}\n")

        # Open Spotify
        open_spotify()
        human_pause(2, 3)

        # Go home first to reset state
        step_go_home()

        # Go to search
        success, screen = step_go_to_search()
        if not success:
            log("❌ Search failed — retrying round")
            continue

        # Type and search
        screen = step_activate_and_type()

        # Tap artist
        success, screen = step_tap_artist(screen)
        if not success:
            log("⚠️  May not be on artist page — continuing anyway")

        # Follow on first round
        if rounds == 1:
            step_follow_artist(screen)

        # Stream songs
        streams = step_stream_songs(screen)
        total_streams += streams

        log(f"\n📊 Round {rounds}: {streams} streams | Total: {total_streams}")

        if total_streams < STREAMS_TARGET:
            pause = random.randint(20, 45)
            log(f"😴 Break: {pause}s...")
            time.sleep(pause)

    log("")
    log("=" * 55)
    log(f"✅ DONE! {total_streams} streams for {ARTIST_NAME}")
    log("=" * 55)

if __name__ == '__main__':
    run()
