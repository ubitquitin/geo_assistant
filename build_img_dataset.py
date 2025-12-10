import json
import os
import requests
from tqdm import tqdm
import csv

# -------------------------------
# CONFIG
# -------------------------------
INPUT_JSON = "usa.json"   # your JSON file
OUTPUT_DIR = "images"
OUTPUT_CSV = "labels.csv"

# Make sure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load JSON
with open(INPUT_JSON, "r") as f:
    data = json.load(f)

# Get the list of entries
entries = data#["customCoordinates"]

# Base API URL
BASE_URL = "https://streetviewpixels-pa.googleapis.com/v1/thumbnail"

# Loop with tqdm progress bar
for entry in tqdm(entries, desc="Downloading images", unit="img"):
    pano_id = entry["panoId"]     # note: camelCase from your JSON
    heading = entry["heading"]

    url = (
        f"{BASE_URL}?panoid={pano_id}"
        f"&cb_client=maps_sv.tactile.gps&w=1024&h=768"
        f"&yaw={heading}&pitch=15&thumbfov=100"
    )

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()

        # Save file as panoid_heading.jpg
        filename = os.path.join(OUTPUT_DIR, f"{pano_id}.jpg")
        with open(filename, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)

    except requests.RequestException as e:
        tqdm.write(f"❌ Failed to fetch panoId={pano_id}, heading={heading}: {e}")

# Write CSV
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)

    # Write header
    writer.writerow(["panoId", "lat", "lng", "heading"])

    # Write rows
    for entry in entries:
        pano_id = entry["panoId"]
        lat = entry["lat"]
        lng = entry["lng"]
        heading = entry["heading"]
        writer.writerow([pano_id, lat, lng, heading])