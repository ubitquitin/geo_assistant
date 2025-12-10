import json
import os
import pickle
import time
import google.generativeai as genai
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def build_vector_db(json_path='meta_database.json', output_path='vector_db.pkl'):
    print("📂 Loading database...")
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # We will flatten the DB into a list of "documents" to embed
    # Structure: {"text": "description...", "country": "Japan", "category": "pole_type"}
    corpus = []

    print("🛠️  Flattening data...")
    for country, categories in data.items():
        for category, items in categories.items():
            # If it's a list of strings
            if isinstance(items, list):
                for item in items:
                    corpus.append({
                        "text": item,
                        "country": country,
                        "category": category
                    })
            # If it's a single string
            elif isinstance(items, str):
                corpus.append({
                    "text": items,
                    "country": country,
                    "category": category
                })

    print(f"🧩 Found {len(corpus)} distinct clues. Generating embeddings...")

    # We batch requests to be efficient
    batch_size = 50
    for i in tqdm(range(0, len(corpus), batch_size)):
        batch = corpus[i : i + batch_size]
        texts = [item["text"] for item in batch]

        try:
            # Use the optimized embedding model
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=texts,
                task_type="retrieval_document"
            )

            # Attach embeddings back to the corpus objects
            for j, embedding in enumerate(result['embedding']):
                batch[j]['embedding'] = embedding

        except Exception as e:
            print(f"❌ Error on batch {i}: {e}")
            time.sleep(2) # Backoff if rate limited

    print(f"💾 Saving vector database to {output_path}...")
    with open(output_path, 'wb') as f:
        pickle.dump(corpus, f)

    print("✅ Done! You can now run the assistant.")

if __name__ == "__main__":
    build_vector_db()