import requests
import json
import time
import os
from tqdm import tqdm

# ==========================================
# CONFIGURATION
# ==========================================
# 1. Your GeoGuessr Session Cookie (Required to create challenges)
#    Go to geoguessr.com -> F12 -> Application -> Cookies -> _ncfa
#    Copy the value of "_ncfa"
NCFA_COOKIE = "mPFqNh34WzF3J68RR9aGZFZRnJfkKEdSCMbx%2FwiRXSs%3DbYyhZsZXIf1itIhX5Isx6%2FOok%2F0MbBjdCmWMvA1bXYn6vvxOglISnsiu94yhUc%2Fg2ATKQQP29O1iC7BNPBlaZ0j2dWoStiomLbDiE8miSos%3D"

# 2. The Map ID you want to scrape
#    Example: "5d73f83d894e6c000161b328" (Extensive Bollards)
#    Example: "62a44b22040f04bd36e8a914" (A Community World)
MAP_ID = "67d85ff8515a6aec219cd249"

# 3. How many unique locations do you want?
TARGET_LOCATIONS = 1000
# ==========================================

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "Cookie": f"_ncfa={NCFA_COOKIE}"
}

def get_challenge_token(map_id):
    """Creates a challenge and returns the token."""
    url = "https://www.geoguessr.com/api/v3/challenges"
    payload = {
        "map": map_id,
        "forbidMoving": True,
        "forbidZooming": True,
        "forbidRotating": True,
        "timeLimit": 10,
        "roundCount": 5
    }
    try:
        r = requests.post(url, json=payload, headers=HEADERS)
        if r.status_code == 200:
            return r.json()['token']
        elif r.status_code == 401:
            print("❌ Error: Unauthorized. Your _ncfa cookie is invalid or expired.")
            exit()
        else:
            print(f"⚠️ Failed to create challenge: {r.status_code}")
            print(f"📜 Error Details: {r.text}")  # <--- THIS IS THE KEY
    except Exception as e:
        print(f"Error: {e}")
    return None

def get_game_data(token):
    """Fetches the game data (including the 5 locations) from the token."""
    url = f"https://www.geoguessr.com/api/v3/games/{token}"
    try:
        r = requests.get(url, headers=HEADERS)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def main():
    print(f"🕷️ Scraping Map: {MAP_ID}")

    unique_panos = set()
    locations = []

    pbar = tqdm(total=TARGET_LOCATIONS)

    while len(locations) < TARGET_LOCATIONS:
        # 1. Generate Challenge
        token = get_challenge_token(MAP_ID)
        if not token:
            time.sleep(2)
            continue

        # 2. Get the 5 rounds
        game_data = get_game_data(token)
        if not game_data:
            continue

        # 3. Extract Locations
        rounds = game_data.get('rounds', [])
        new_found = 0

        for rnd in rounds:
            pano = rnd.get('panoId')
            if pano and pano not in unique_panos:
                unique_panos.add(pano)

                locations.append({
                    "panoId": pano,
                    "lat": rnd['lat'],
                    "lng": rnd['lng'],
                    "heading": rnd.get('heading', 0),
                    "pitch": rnd.get('pitch', 0)
                })
                new_found += 1
                pbar.update(1)

        # Be nice to the API
        time.sleep(1.0)

    pbar.close()

    # Save to JSON
    output_file = f"scraped_{MAP_ID}.json"
    with open(output_file, "w") as f:
        json.dump(locations, f, indent=4)

    print(f"\n✅ Saved {len(locations)} locations to {output_file}")
    print("👉 Now run your image downloader script on this file.")

if __name__ == "__main__":
    main()