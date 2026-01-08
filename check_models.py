from google import genai
import os
from dotenv import load_dotenv
import sys

# Force unbuffered output
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("API_KEY not found")
else:
    client = genai.Client(api_key=api_key)
    try:
        print("--- START MODEL LIST ---")
        for m in client.models.list():
            print(f"{m.name}")
        print("--- END MODEL LIST ---")
    except Exception as e:
        print(f"Error listing models: {e}")
