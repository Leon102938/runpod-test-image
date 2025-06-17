# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from PIL import Image, ImageDraw
import uuid, os

app = FastAPI()

class Txt2ImgRequest(BaseModel):
    prompt: str

@app.post("/generate")
def generate_image(data: Txt2ImgRequest):
    img = Image.new('RGB', (512, 512), color='black')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), data.prompt, fill=(255, 255, 0))
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/{uuid.uuid4().hex}.png"
    img.save(path)
    return {"image_path": path}
