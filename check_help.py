from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

try:
    import inspect
    sig = inspect.signature(client.models.generate_videos)
    for name in sig.parameters:
        print(f"PARAM: {name}")
except Exception as e:
    print(e)
