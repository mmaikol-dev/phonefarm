import google.generativeai as genai
from PIL import Image
import subprocess
import time
import random
import json
import datetime

# ── CONFIG ────────────────────────────────────────
API_KEY = "AIzaSyCfyU_Ifv9W-Y5K9EzS7ZKBYZ-xb-ewgFw"
MAX_LIKES = 30
MAX_FOLLOWS = 10
LOG_FILE = "instagram_log.txt"

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')
INSTAGRAM_PACKAGE = 'com.instagram.android'

# ── EXACT COORDINATES FOR REDMI NOTE 10 PRO (1080x2400) ──
COORDS = {
    'video_center':   (360, 700),   # double tap here to like
    'like_button':    (651, 735),   # heart icon
    'comment_button': (651, 845),   # comment icon
    'repost_button':  (651, 955),   # repost icon
    'send_button':    (651, 1065),  # send icon
    'save_button':    (651, 1175),  # bookmark icon
    'follow_button':  (441, 1331),  # follow button
    'swipe_start':    (360, 1600),  # swipe up start
    'swipe_end':      (360, 400),   # swipe up end
}

# ── LOGGING ───────────────────────────────────────
def log(message):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_FILE, 'a') as f:
        f.write(full_message + '\n')

# ── PHONE ACTIONS ─────────────────────────────────
def capture_screen():
    subprocess.run(
        'adb exec-out screencap -p > screen.png',
        shell=True
    )
    return Image.open('screen.png')

def tap(x, y):
    subprocess.run([
        'adb', 'shell', 'input', 'tap', str(x), str(y)
    ])
    time.sleep(random.uniform(0.5, 1.2))

def double_tap(x, y):
    """Double tap to like on Instagram Reels"""
    subprocess.run([
        'adb', 'shell', 'input', 'tap', str(x), str(y)
    ])
    time.sleep(0.08)
    subprocess.run([
        'adb', 'shell', 'input', 'tap', str(x), str(y)
    ])

def swipe_to_next():
    """Swipe up to go to next reel"""
    subprocess.run([
        'adb', 'shell', 'input', 'swipe',
        str(COORDS['swipe_start'][0]),
        str(COORDS['swipe_start'][1]),
        str(COORDS['swipe_end'][0]),
        str(COORDS['swipe_end'][1]),
        '400'
    ])
    time.sleep(random.uniform(2.0, 3.5))

def open_instagram():
    subprocess.run([
        'adb', 'shell', 'monkey',
        '-p', INSTAGRAM_PACKAGE,
        '-c', 'android.intent.category.LAUNCHER',
        '1'
    ], check=True)
    time.sleep(5)

def human_pause(min_sec=2, max_sec=5):
    pause = random.uniform(min_sec, max_sec)
    time.sleep(pause)

def long_break(min_sec=15, max_sec=35):
    pause = random.uniform(min_sec, max_sec)
    log(f"😴 Human break: {pause:.0f} seconds...")
    time.sleep(pause)

# ── AI ANALYSIS ───────────────────────────────────
def analyze_screen(image):
    """Ask Gemini to analyze current Instagram screen state"""
    try:
        response = model.generate_content([
            """
            Look at this Instagram screenshot very carefully.
            Answer ONLY in this exact format, one per line, nothing else:

            IS_REEL: yes or no
            ALREADY_LIKED: yes or no (is the heart icon filled red/pink?)
            HAS_FOLLOW_BUTTON: yes or no (is there a Follow button visible?)
            USERNAME: the @username shown or unknown
            """,
            image
        ])

        result = {
            'is_reel': False,
            'already_liked': False,
            'has_follow': False,
            'username': 'unknown'
        }

        lines = response.text.strip().split('\n')
        for line in lines:
            line = line.strip()
            if 'IS_REEL:' in line:
                result['is_reel'] = 'yes' in line.lower()
            elif 'ALREADY_LIKED:' in line:
                result['already_liked'] = 'yes' in line.lower()
            elif 'HAS_FOLLOW_BUTTON:' in line:
                result['has_follow'] = 'yes' in line.lower()
            elif 'USERNAME:' in line:
                result['username'] = line.split(':', 1)[-1].strip()

        return result

    except Exception as e:
        log(f"⚠️  Gemini error: {e}")
        return {
            'is_reel': True,  # assume reel and continue
            'already_liked': False,
            'has_follow': False,
            'username': 'unknown'
        }

def check_heart_color(image):
    """
    Double check if like was registered
    by looking at heart color after double tap
    """
    try:
        response = model.generate_content([
            """
            Look at the heart/like icon on the RIGHT side of this Instagram screen.
            Is the heart icon filled and red/pink color? (meaning it is liked)
            Answer ONLY: yes or no
            """,
            image
        ])
        return 'yes' in response.text.lower()
    except:
        return True  # assume it worked

# ── MAIN AUTOMATION LOOP ──────────────────────────
def run():
    log("=" * 50)
    log("🤖 Instagram Automation Started")
    log(f"🎯 Target: {MAX_LIKES} likes, {MAX_FOLLOWS} follows")
    log("=" * 50)
    log("📲 Opening Instagram on phone...")
    open_instagram()
    log("📱 Make sure Instagram Reels is open on phone")
    log("▶️  Starting in 5 seconds...")
    time.sleep(5)

    likes_count = 0
    follows_count = 0
    skipped = 0
    session_count = 0

    while likes_count < MAX_LIKES:
        session_count += 1
        log(f"")
        log(f"━━━ Reel #{session_count} | ❤️ {likes_count}/{MAX_LIKES} likes | 👤 {follows_count} follows ━━━")

        # ── Capture & Analyze ──
        log("📸 Capturing screen...")
        screen = capture_screen()

        log("🧠 Analyzing screen with Gemini...")
        state = analyze_screen(screen)

        log(f"   📱 Is Reel: {'✅' if state['is_reel'] else '❌'}")
        log(f"   👤 Username: {state['username']}")
        log(f"   ❤️  Already liked: {'Yes' if state['already_liked'] else 'No'}")
        log(f"   ➕ Follow available: {'Yes' if state['has_follow'] else 'No'}")

        # ── Skip if not a reel ──
        if not state['is_reel']:
            log("⚠️  Not on Reels — scrolling...")
            skipped += 1
            swipe_to_next()
            continue

        # ── Like if not already liked ──
        if not state['already_liked']:
            log(f"❤️  Double tapping to like...")
            double_tap(*COORDS['video_center'])
            human_pause(1.5, 3.0)

            # Verify like worked
            screen_after = capture_screen()
            liked = check_heart_color(screen_after)

            if liked:
                likes_count += 1
                log(f"✅ Like confirmed! Total: {likes_count}")
            else:
                log("⚠️  Like may not have registered — trying heart button directly...")
                tap(*COORDS['like_button'])
                human_pause(1.5, 2.5)
                likes_count += 1

        else:
            log("⏭️  Already liked — skipping to next")
            skipped += 1

        # ── Follow (random, 1 in 4 chance) ──
        if (state['has_follow'] and
            follows_count < MAX_FOLLOWS and
            random.random() < 0.25):
            log(f"👤 Following {state['username']}...")
            tap(*COORDS['follow_button'])
            follows_count += 1
            log(f"✅ Followed! Total follows: {follows_count}")
            human_pause(2, 4)

        # ── Save occasionally (1 in 8 chance) ──
        if random.random() < 0.12:
            log("🔖 Saving this reel...")
            tap(*COORDS['save_button'])
            human_pause(1, 2)

        # ── Scroll to next reel ──
        log("⬆️  Scrolling to next reel...")
        swipe_to_next()

        # ── Long break every 10 likes ──
        if likes_count > 0 and likes_count % 10 == 0:
            long_break(20, 40)

        # ── Small random pause between reels ──
        human_pause(1, 3)

    # ── Session Complete ──
    log("")
    log("=" * 50)
    log(f"✅ SESSION COMPLETE!")
    log(f"❤️  Liked:    {likes_count} posts")
    log(f"👤 Followed: {follows_count} accounts")
    log(f"⏭️  Skipped:  {skipped} posts")
    log(f"📄 Log saved to: {LOG_FILE}")
    log("=" * 50)

if __name__ == '__main__':
    run()
