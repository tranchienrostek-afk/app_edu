from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

if not api_key:
    print("API_KEY not found")
else:
    client = genai.Client(api_key=api_key)
    print("Methods in client.models:")
    print(dir(client.models))
