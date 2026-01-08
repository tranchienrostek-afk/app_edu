import time
from google import genai
import traceback
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../.env")

try:
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("WARNING: API_KEY not found in env")
    client = genai.Client(api_key=api_key)
    
    prompt = "Panning wide shot of a calico kitten sleeping in the sunshine"
    
    # Step 1: Generate an image with Nano Banana.
    print("Step 1: Image Gen")
    image = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt,
        config={"response_modalities":['IMAGE']}
    )
    
    # Step 2: Generate video with Veo 3.1 using the image.
    print("Step 2: Video Gen")
    img_input = image.parts[0].as_image()
    print(f"Image type: {type(img_input)}")
    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        prompt=prompt,
        image=img_input,
    )
    
    # Poll the operation status until the video is ready.
    while not operation.done:
        print("Waiting for video generation to complete...")
        time.sleep(10)
        operation = client.operations.get(operation)
    
    # Download the video.
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)
    video.video.save("veo3_with_image_input.mp4")
    print("Generated video saved to veo3_with_image_input.mp4")

except Exception as e:
    print(f"FATAL ERROR: {e}")
    with open("traceback.log", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())
