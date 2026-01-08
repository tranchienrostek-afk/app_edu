from google import genai
from google.genai import types
from PIL import Image
import io

print("Checking types.Image...")
try:
    # Create a dummy image
    img = Image.new('RGB', (100, 100), color = 'red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    # Try different constructors
    print(f"types.Image: {types.Image}")
    
    # Try instantiation if possible, or print doc
    with open("type_test.log", "w") as log:
        try:
            t_img = types.Image(image_bytes=img_bytes)
            log.write("Success: types.Image(image_bytes=...)\n")
        except Exception as e:
            log.write(f"Failed (image_bytes): {e}\n")

        try:
            t_img = types.Image(data=img_bytes, mime_type="image/png")
            log.write("Success: types.Image(data=..., mime_type=...)\n") 
        except Exception as e:
             log.write(f"Failed (data, mime_type): {e}\n")
        
        # Check introspection
        import inspect
        sig = inspect.signature(types.Image)
        log.write(f"Signature: {sig}\n")

except Exception as e:
    print(e)
