from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("API_KEY not found")
else:
    client = genai.Client(api_key=api_key)
    print("--- SEARCHING FOR IMAGEN MODELS ---")
    try:
        for m in client.models.list():
            if "imagen" in m.name.lower() or "image" in m.name.lower():
                print(f"Found: {m.name}")
    except Exception as e:
        print(f"Error: {e}")
    print("--- END SEARCH ---")
