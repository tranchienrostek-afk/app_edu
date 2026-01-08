from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("API_KEY not found")
else:
    client = genai.Client(api_key=api_key)
    
    models_to_test = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-latest",
        "gemini-2.0-flash-exp",
        "veo-3.1-generate-preview"
    ]

    print("--- START TEST ---")
    for model_name in models_to_test:
        try:
            print(f"Testing {model_name}...")
            # We just want to check if it exists, so a simple list check or dummy generation
            # But list is better if generate takes tokens.
            # However generate is the ultimate test.
            
            response = client.models.generate_content(
                model=model_name,
                contents="Hello",
            )
            print(f"[SUCCESS] {model_name}: OK")
        except Exception as e:
            print(f"[FAILURE] {model_name}: {e}")
    print("--- END TEST ---")
