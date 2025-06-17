import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def generate_image(prompt: str) -> str:
    # Erstelle Dummy-Bild mit Prompt als Text
    img = Image.new('RGB', (512, 512), color=(73, 109, 137))
    d = ImageDraw.Draw(img)
    d.text((10,10), prompt, fill=(255,255,0))

    # Speicherpfad
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    path = f"/workspace/generated_{timestamp}.png"
    img.save(path)

    return path
