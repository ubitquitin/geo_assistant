import os
import json
import pickle
import mss
import time
import numpy as np
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# 1. SETUP
load_dotenv()
genai.configure(api_key="AIzaSyDlrEhczFqkoXWJBD1cq8k-q-tO-HGuhSU")

# Use Flash for speed, or Pro for higher reasoning/detail
model = genai.GenerativeModel('gemini-2.5-flash')

class GeoGuessrAssistant:
    def __init__(self, vector_db_path='vector_db.pkl'):
        self.sct = mss.mss()
        self.vector_db = self._load_vector_db(vector_db_path)

    def _load_vector_db(self, path):
        try:
            with open(path, 'rb') as f:
                print(f"🧠 Loaded Vector Knowledge Base from {path}")
                return pickle.load(f)
        except FileNotFoundError:
            print("❌ Vector DB not found! Run 'build_embeddings.py' first.")
            exit()

    def capture_screen(self):
        # (Keep your existing working screen capture code here)
        # Assuming Windows/MSS for now:
        monitor = self.sct.monitors[1]
        sct_img = self.sct.grab(monitor)
        return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

    def extract_visual_clues(self, image):
        prompt = """
        Analyze this GeoGuessr screenshot.

        PART 1: VISUAL META
        Describe these features in technical detail if visible:
        - Utility Poles (material, shape, insulators)
        - Bollards (shape, colors, reflector)
        - Road Lines (color, pattern)
        - License Plates (color, shape)

        PART 2: TEXT & LANGUAGE
        - Transcribe any visible text (signs, billboards, shopfronts).
        - Identify the language or script (e.g. "Thai", "Cyrillic", "Polish").
        - Extract any potential city or region names found in the text.

        Return JSON format:
        {
            "pole_type": "description...",
            "bollard_type": "description...",
            "road_lines": "description...",
            "plates": "description...",
            "visible_text": "Transcribed text here (or 'None')",
            "language_guess": "Language name (or 'None')",
            "city_names": "City names found (or 'None')"
        }
        """
        try:
            response = model.generate_content([prompt, image])
            text = response.text.replace('```json', '').replace('```', '').strip()
            return json.loads(text)
        except Exception as e:
            print(f"Vision Error: {e}")
            return {}

    def get_embedding(self, text):
        """Generates embedding for the user's observed clue."""
        if not text or len(text) < 3: return None
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query"
        )
        return result['embedding']

    def semantic_search(self, category, user_description):
        """
        Finds the closest match in the vector DB for a specific category.
        """
        user_vector = self.get_embedding(user_description)
        if not user_vector: return []

        scores = []

        # Filter DB to only look at relevant category (e.g. only compare poles to poles)
        # This reduces noise significantly.
        relevant_docs = [doc for doc in self.vector_db if doc['category'] == category]

        if not relevant_docs: return []

        # Vector Math: Cosine Similarity
        # (Dot product of normalized vectors)
        for doc in relevant_docs:
            doc_vec = doc['embedding']
            score = np.dot(user_vector, doc_vec) # range -1 to 1
            if score > 0.55: # Threshold to ignore noise
                scores.append((doc['country'], doc['text'], score))

        # Sort by highest score
        return sorted(scores, key=lambda x: x[2], reverse=True)[:3]

    def run(self):
        print("✅ System Ready. Press Enter to scan...")
        while True:
            cmd = input("\n[Enter] to scan, [q] to quit: ")
            if cmd.lower() == 'q': break

            print("👁️  Scanning...")
            img = self.capture_screen()
            clues = self.extract_visual_clues(img)

            print("\n--- ANALYSIS ---")

            # 1. NEW: Handle Text & Language First
            if clues.get('visible_text') and clues['visible_text'].lower() != "none":
                print(f"🔤 TEXT FOUND:  \"{clues['visible_text']}\"")
                print(f"🗣️  LANGUAGE:    {clues.get('language_guess', 'Unknown')}")

                if clues.get('city_names') and clues['city_names'].lower() != "none":
                    print(f"🏙️  CITY/REGION: {clues['city_names']} (High Confidence Location!)")

            # 2. Existing Semantic Search Logic
            country_scores = {}

            # We skip searching for "visible_text" in the pole database (it wouldn't match).
            # We only search the visual categories.
            visual_categories = ["pole_type", "bollard_type", "road_lines", "plates"]

            for category in visual_categories:
                description = clues.get(category)
                if description and description.lower() != "none":
                    print(f"\n🔎 Analyzing {category}: '{description}'")
                    matches = self.semantic_search(category, description)

                    for country, text, score in matches:
                        print(f"   ↳ Match: {country} ({score:.2f})")
                        country_scores[country] = country_scores.get(country, 0) + score

            # 3. Final Ranking
            print("\n🏆 FINAL PREDICTION:")
            if not country_scores:
                print("   (No strong database matches. Rely on Language/Text above.)")
            else:
                sorted_countries = sorted(country_scores.items(), key=lambda x: x[1], reverse=True)
                for country, total_score in sorted_countries[:3]:
                    print(f"   {country} (Score: {total_score:.2f})")

if __name__ == "__main__":
    assistant = GeoGuessrAssistant()
    assistant.run()