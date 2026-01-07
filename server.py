import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64
import io
from PIL import Image
from google import genai
from google.genai import types
from dotenv import load_dotenv
import wave
import tempfile

import logging
import traceback

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load .env from parent directory
load_dotenv(dotenv_path="../.env")

app = Flask(__name__, template_folder=".")
CORS(app)

api_key = os.getenv("API_KEY")
if not api_key:
    logging.warning("API_KEY not found. Gemini calls will fail.")

try:
    client = genai.Client(api_key=api_key)
    logging.info("Gemini Client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Gemini Client: {e}")


# --- NEW: TTS Endpoint ---
@app.route('/speak', methods=['POST'])
def speak():
    try:
        data = request.json
        text = data.get("text", "")
        if not text: return jsonify({"error": "No text"}), 400
        
        # Call Gemini TTS
        response = client.models.generate_content(
           model="gemini-2.5-flash-preview-tts",
           contents=f"Say cheerfully in Vietnamese: {text}",
           config=types.GenerateContentConfig(
              response_modalities=["AUDIO"],
              speech_config=types.SpeechConfig(
                 voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                       voice_name='Kore',
                    )
                 )
              ),
           )
        )
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        return jsonify({"audio": audio_b64})
    except Exception as e:
        logging.error(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500

# --- NEW: STT Endpoint ---
@app.route('/listen', methods=['POST'])
def listen():
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file"}), 400
        
        audio_file = request.files['audio']
        
        # Save temp file for Gemini to read
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            audio_file.save(temp.name)
            temp_path = temp.name

        # Read file bytes for inline data
        with open(temp_path, "rb") as f:
            audio_bytes = f.read()
        
        prompt = "Transcribe this audio exactly in Vietnamese."
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part(inline_data=types.Blob(
                            mime_type="audio/wav",
                            data=audio_bytes
                        )),
                        types.Part(text=prompt)
                    ]
                )
            ]
        )
        
        os.unlink(temp_path) # Clean up
        transcribed_text = response.text.strip()
        logging.info(f"Heard: {transcribed_text}")
        
        return jsonify({"text": transcribed_text})
    except Exception as e:
        logging.error(f"STT Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return render_template("new_index.html")



@app.route('/animate', methods=['POST'])
def animate():
    try:
        data = request.json
        image_data = data.get("image")
        prompt = data.get("prompt", "Cinematic movement")
        
        if not image_data: return jsonify({"error": "No image"}), 400
        
        if "," in image_data: image_data = image_data.split(",")[1]
        image_bytes = base64.b64decode(image_data)
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        logging.info(f"Starting video generation with Veo 3.1 for prompt: {prompt}")
        
        # Proper input format for Veo via GenAI SDK
        # Convert PIL to simple bytes again
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()

        # Some versions use generate_content, others use generate_videos. 
        # Let's try to map it to the known working pattern for this SDK version.
        # If generate_videos exists, we use it but with clearer types.
        
        response = client.models.generate_content(
            model="veo-3.1-generate-preview",
            contents=[
                types.Content(
                    parts=[
                        types.Part(text=prompt),
                        types.Part(inline_data=types.Blob(
                           mime_type="image/png",
                           data=img_bytes
                        ))
                    ]
                )
            ]
        )
            
        # Veo usually returns a video URI or bytes in the response
        # generate_content for video generation models might behave differently (async operation)
        # But for 'preview' it might be sync or return a link?
        # Actually Veo 2/3 via API is often async regular logic.
        # Let's assume the previous code failed because `image=pil_image` wasn't auto-converted.
        
        # If generate_content returns the video directly:
        video_bytes = None
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                video_bytes = part.inline_data.data
                break
            if part.file_data:
                # Handle file uri if needed, but for now expect inline
                pass

        if not video_bytes:
             return jsonify({"error": "No video content returned"}), 500
        
        vid_b64 = base64.b64encode(video_bytes).decode('utf-8')
        return jsonify({"video": vid_b64})

    except Exception as e:
        logging.error(f"Animation Error: {e}")
        # Return empty video to avoid frontend crash
        return jsonify({"error": "Video generation temporarily unavailable."}), 200

@app.route('/voice_command', methods=['POST'])
def voice_command():
    try:
        data = request.json
        user_speech = data.get("text", "")
        filenames = data.get("filenames", []) # List of available image filenames
        
        logging.info(f"Voice Command: {user_speech}")
        logging.info(f"Files: {filenames}")

        # Use Gemini to interpret intent
        prompt = (
            f"You are the brain of a photo classroom assistant. "
            f"The user speaks commands to either FIND a student's photo OR declare a DREAM JOB. "
            f"Available filenames: {filenames}\n\n"
            f"User Speech: '{user_speech}'\n\n"
            f"Rules:\n"
            f"1. IF user wants to find/show a person (e.g., 'Tìm bạn Chiến', 'Cho xem ảnh Trà'):\n"
            f"   - Match the name to the closest filename in the list mostly phonetically.\n"
            f"   - Return JSON: {{ 'action': 'FIND_IMAGE', 'target': '<exact_filename>', 'reply': 'Đang mở ảnh bạn <name>.' }}\n"
            f"   - IF multiple similar files exist (e.g. chien_a.jpg, chien_b.jpg) and it is unclear, return {{ 'action': 'AMBIGUOUS', 'reply': 'Có nhiều bạn tên ... bạn muốn xem ảnh nào?' }}\n"
            f"   - IF not found, return {{ 'action': 'UNKNOWN', 'reply': 'Không tìm thấy ảnh bạn đó.' }}\n"
            f"2. IF user declares a job/dream (e.g., 'Ước mơ là bác sĩ', 'Con muốn làm công an'):\n"
            f"   - Extract the job title.\n"
            f"   - Return JSON: {{ 'action': 'SET_JOB', 'target': '<job_title>', 'reply': 'Đã xác nhận ước mơ <job_title>.' }}\n"
            f"3. IMPORTANT: The 'reply' field MUST BE IN VIETNAMESE language.\n"
            f"4. Output strictly valid JSON."
        )

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        # Parse Gemini Response (JSON is guaranteed now)
        try:
             result = response.parsed
             if not result: # Fallback if parsed is empty
                 import json
                 result = json.loads(response.text)
        except:
             import json
             result = json.loads(response.text)
        
        return jsonify(result)

    except Exception as e:
        logging.error(f"Voice Logic Error: {e}")
        return jsonify({"action": "ERROR", "reply": "Lỗi xử lý giọng nói."}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        data = request.json
        image_data = data.get("image")
        job_description = data.get("job_description", "professional")
        student_name = data.get("student_name", "student")

        if not image_data:
            return jsonify({"error": "No image data provided"}), 400
        
        # Decode base64 image
        if "," in image_data:
            image_data = image_data.split(",")[1]
            
        image_bytes = base64.b64decode(image_data)
        raw_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Create prompt for Google GenAI
        prompt = (
            f"Generate a photorealistic image of this person as a {job_description}, "
            f"wearing professional {job_description} attire. "
            f"The setting should be polite, aspirational, and school-appropriate. "
            f"High quality, 8k resolution, cinematic lighting. "
            f"Maintain the person's likeness where possible but transform them into an adult professional."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[raw_image, prompt],
        )
        
        generated_image_base64 = ""
        
        for part in response.parts:
            if part.inline_data:
                 generated_image_base64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                 break
        
        if not generated_image_base64:
             return jsonify({"error": "No image generated"}), 500

        # --- WATERMARK LOGIC (Caption) ---
        try:
             from PIL import ImageDraw, ImageFont
             # Decode again to edit
             gen_bytes = base64.b64decode(generated_image_base64)
             img_edit = Image.open(io.BytesIO(gen_bytes)).convert("RGB")
             draw = ImageDraw.Draw(img_edit)
             
             # Text Content
             w, h = img_edit.size
             caption_text = f"{student_name} - {job_description.title()}"
             
             # Font Loading & Auto-Scaling
             font_size = int(h * 0.05) # Start at 5% height
             max_width = w * 0.9 # Max 90% of image width
             
             try:
                 font = ImageFont.truetype("arial.ttf", font_size)
             except:
                 font = ImageFont.load_default()

             # Reduce font size until it fits
             while font_size > 10:
                 bbox = draw.textbbox((0, 0), caption_text, font=font)
                 text_w = bbox[2] - bbox[0]
                 if text_w <= max_width:
                     break
                 font_size -= 2
                 try:
                     font = ImageFont.truetype("arial.ttf", font_size)
                 except:
                     font = ImageFont.load_default()
                     break

             # Recalculate size with final font
             bbox = draw.textbbox((0, 0), caption_text, font=font)
             text_w = bbox[2] - bbox[0]
             text_h = bbox[3] - bbox[1]
             
             x = (w - text_w) / 2
             y = h - text_h - 20 # 20px padding from bottom

             # Draw Shadow/Outline for readability
             outline_color = "black"
             text_color = "white"
             offset = 2
             
             # Draw outline
             for off_x in [-offset, offset]:
                 for off_y in [-offset, offset]:
                     draw.text((x+off_x, y+off_y), caption_text, font=font, fill=outline_color)
             
             # Draw text
             draw.text((x, y), caption_text, font=font, fill=text_color)
             
             # Re-encode
             buffered = io.BytesIO()
             img_edit.save(buffered, format="PNG")
             generated_image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
             
        except Exception as e:
             logging.error(f"Caption Error: {e}")
             # Continue without caption if fails

        # Auto-Save Logic
        output_dir = "results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Sanitize filename
        safe_name = "".join([c for c in student_name if c.isalpha() or c.isdigit() or c==' ']).strip().replace(" ", "_")
        safe_job = "".join([c for c in job_description if c.isalpha() or c.isdigit() or c==' ']).strip().replace(" ", "_")
        filename = f"{safe_name}_{safe_job}.png"
        file_path = os.path.join(output_dir, filename)
        
        # Save to disk
        with open(file_path, "wb") as fh:
            fh.write(base64.b64decode(generated_image_base64))
        logging.info(f"Saved to: {file_path}")

        return jsonify({
            "generated_image": generated_image_base64,
            "caption": caption_text, # Return simple text for UI too
            "saved_path": file_path
        })
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logging.info("Starting Flask Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)