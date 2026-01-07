import torch
from diffusers import AutoPipelineForImage2Image

MODEL_ID = "stabilityai/sdxl-turbo"
print(f"Downloading {MODEL_ID}...")

# Download and cache the model
pipe = AutoPipelineForImage2Image.from_pretrained(
    MODEL_ID, 
    torch_dtype=torch.float16, 
    variant="fp16"
)

print("Download complete! Model is cached.")
