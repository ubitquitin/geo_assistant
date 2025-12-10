import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load your key
load_dotenv()

# Or hardcode it if you prefer:
# genai.configure(api_key="AIzaSy...")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("Querying Google for available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")