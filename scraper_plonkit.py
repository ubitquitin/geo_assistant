import json
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# List of countries to scrape (You can add more)
COUNTRIES = [
    "japan", "poland", "south-korea", "taiwan", "thailand",
    "indonesia", "malaysia", "singapore", "philippines",
    "cambodia", "sri-lanka", "bangladesh", "kyrgyzstan",
    "brazil", "argentina", "chile", "uruguay", "bolivia",
    "peru", "colombia", "ecuador", "mexico", "guatemala",
    "australia", "new-zealand", "south-africa", "kenya",
    "ghana", "nigeria", "senegal", "tunisia", "botswana",
    "united-kingdom", "ireland", "france", "germany",
    "netherlands", "belgium", "denmark", "norway",
    "sweden", "finland", "estonia", "latvia", "lithuania",
    "russia", "ukraine", "romania", "bulgaria", "hungary",
    "czech-republic", "slovakia", "slovenia", "croatia",
    "serbia", "montenegro", "north-macedonia", "albania",
    "greece", "turkey", "israel", "jordan", "united-arab-emirates"
]

def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def clean_text(text):
    """Removes extra whitespace and newlines."""
    return re.sub(r'\s+', ' ', text).strip()

def scrape_country(driver, country):
    url = f"https://www.plonkit.net/{country}"
    print(f"   Fetching {url}...")

    try:
        driver.get(url)
        # Wait for React to hydrate the page
        time.sleep(3)

        # Scroll down to trigger lazy loading of images/text
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # PlonkIt structure varies, but usually uses standard headers
        # We will extract all text paragraphs following specific headers
        data = {
            "pole_type": [],
            "road_lines": [],
            "bollard_type": [],
            "plates": [],
            "driving_side": [],
            "unique_features": [],
            "landscape": []
        }

        # Basic Heuristic: Find all text blocks and categorize them by keywords
        # This is "loose" scraping because class names are dynamic/obfuscated
        all_text = [clean_text(p.get_text()) for p in soup.find_all(['p', 'li', 'h4'])]

        for text in all_text:
            text_lower = text.lower()

            # Categorize the text based on keywords
            if "pole" in text_lower:
                data["pole_type"].append(text)
            elif "line" in text_lower or "road marking" in text_lower:
                data["road_lines"].append(text)
            elif "bollard" in text_lower or "reflector" in text_lower:
                data["bollard_type"].append(text)
            elif "plate" in text_lower and ("license" in text_lower or "registration" in text_lower):
                data["plates"].append(text)
            elif "drive" in text_lower and ("left" in text_lower or "right" in text_lower):
                data["driving_side"].append(text)
            elif "landscape" in text_lower or "vegetation" in text_lower or "trees" in text_lower:
                data["landscape"].append(text)

        # Deduplicate list
        for k in data:
            data[k] = list(set(data[k]))

        return data

    except Exception as e:
        print(f"   Error scraping {country}: {e}")
        return None

def main():
    print("🚀 Starting PlonkIt Scraper...")
    driver = setup_driver()

    full_database = {}

    for i, country in enumerate(COUNTRIES):
        print(f"[{i+1}/{len(COUNTRIES)}] Scraping {country.upper()}...")
        country_data = scrape_country(driver, country)
        if country_data:
            # Clean up the country name for the DB key
            db_key = country.replace("-", " ").title()
            full_database[db_key] = country_data

    driver.quit()

    # Save to file
    with open('meta_database.json', 'w', encoding='utf-8') as f:
        json.dump(full_database, f, indent=4, ensure_ascii=False)

    print("\n✅ Database generated: 'meta_database.json'")

if __name__ == "__main__":
    main()