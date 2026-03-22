import google.generativeai as genai

from PIL import Image

import subprocess

import time

import random

import json

genai.configure(api_key="AIzaSyCfyU_Ifv9W-Y5K9EzS7ZKBYZ-xb-ewgFw")

model = genai.GenerativeModel('gemini-3-flash-preview')

def capture_screen():

    subprocess.run('adb exec-out screencap -p > screen.png', shell=True)

    return Image.open('screen.png')

def tap(x, y):

    subprocess.run(['adb', 'shell', 'input', 'tap', str(x), str(y)])

    time.sleep(random.uniform(0.5, 1.5))

def swipe_up():

    subprocess.run([

        'adb', 'shell', 'input', 'swipe',

        '500', '1200', '500', '300', '400'

    ])

    time.sleep(random.uniform(1.5, 3.0))

def ask_gemini(image, prompt):

    response = model.generate_content([prompt, image])

    return response.text

def get_like_button_coords(image):

    response = ask_gemini(image, """

    Look at this Instagram screenshot.

    Find the LIKE button (heart icon).

    

    Respond ONLY in JSON format like this:

    {"found": true, "x": 123, "y": 456, "already_liked": false}

    

    If already liked (heart is filled/red), set already_liked to true.

    If not found, set found to false.

    Only respond with JSON, nothing else.

    """)

    

    try:

        # Clean response and parse JSON

        clean = response.strip().replace('```json','').replace('```','')

        return json.loads(clean)

    except:

        return {"found": False}

# ── MAIN LOOP ─────────────────────────────────────

print("🤖 Instagram Auto-Liker Starting...")

print("⚠️  Make sure Instagram Reels is open on phone")

print("Starting in 3 seconds...")

time.sleep(3)

likes_count = 0

max_likes = 20  # limit per session

while likes_count < max_likes:

    print(f"\n📱 Capturing screen... (Likes so far: {likes_count})")

    screen = capture_screen()

    

    print("🔍 Looking for Like button...")

    result = get_like_button_coords(screen)

    

    if result.get('found') and not result.get('already_liked'):

        x = result['x']

        y = result['y']

        print(f"❤️  Liking post... tapping at ({x}, {y})")

        tap(x, y)

        likes_count += 1

        

        # Human pause after liking

        time.sleep(random.uniform(2, 4))

        

    elif result.get('already_liked'):

        print("⏭️  Already liked, scrolling...")

    else:

        print("❓ Like button not found, scrolling...")

    

    # Scroll to next reel

    print("⬆️  Scrolling to next reel...")

    swipe_up()

    

    # Random longer pause every 5 likes

    if likes_count % 5 == 0 and likes_count > 0:

        pause = random.uniform(10, 20)

        print(f"😴 Taking a human break for {pause:.0f} seconds...")

        time.sleep(pause)

print(f"\n✅ Session complete! Liked {likes_count} posts.")
