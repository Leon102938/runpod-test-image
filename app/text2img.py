# 🎨 TEXT2IMG: Generiert ein Bild aus Prompt + Style
import uuid
from PIL import Image, ImageDraw

def generate_image(prompt: str, style: str) -> str:
    # 🔧 Dummy-Logik (hier später echtes Modell rein)
    filename = f"/workspace/generated/{uuid.uuid4().hex}.png"
    image = Image.new("RGB", (512, 512), color="white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), f"{prompt}\nStyle: {style}", fill="black")
    image.save(filename)
    return filename  # ✅ Wird als Bild-URL zurückgegeben

