# 🚀 FASTAPI SERVER – NUR FÜR txt2img

# 📦 INSTALLATIONEN & IMPORTS
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn

# 🧠 TOOL IMPORT | TXT2IMG ONLY
from text2img import generate_image_from_json

# 🚀 FASTAPI APP INITIALISIEREN
app = FastAPI()

# 📄 DATENSTRUKTUR | TXT2IMG INPUT MODELL
class Txt2ImgRequest(BaseModel):
    # 1. Standard
    prompt: str
    negative_prompt: Optional[str] = ""
    model: Optional[str] = "absolutereality"

    # 2. Advanced Settings
    width: Optional[int] = 832
    height: Optional[int] = 1242
    steps: Optional[int] = 30
    cfg: Optional[float] = 7.0
    sampler: Optional[str] = "Euler"
    seed: Optional[int] = None

    # 3. Upscale
    upscale: Optional[bool] = False

    # 4. Output path (optional)
    output_path: Optional[str] = None

    # 5. LoRAs (Platzhalter)
    loras: Optional[list] = []

    # 6. ControlNet (Platzhalter)
    controlnet: Optional[dict] = {}

# 🔁 TOOL ENDPOINT | TXT2IMG
@app.post("/txt2img")
async def txt2img_route(request: Request):
    data = await request.json()
    image_path = generate_image_from_json(data)
    return {"output": image_path}
