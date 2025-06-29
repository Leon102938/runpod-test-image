# 🚀 FASTAPI SERVER – NUR FÜR txt2img

# 📦 INSTALLATIONEN & IMPORTS
from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import uvicorn

# 📂 TOOL IMPORT – TXT2IMG ONLY
from txt2img import generate_image_from_json

# 🌐 FASTAPI APP INITIALISIEREN
app = FastAPI()

# 🧩 DATENSTRUKTUR – TXT2IMG INPUT MODELL
class Txt2ImgRequest(BaseModel):
    # 1_Standard
    prompt: str
    negative_prompt: Optional[str] = ""
    model: Optional[str] = "absolutereality"

    # 4_Advanced_Settings
    width: Optional[int] = 832
    height: Optional[int] = 1242
    steps: Optional[int] = 30
    cfg: Optional[float] = 7.0
    sampler: Optional[str] = "Euler"
    seed: Optional[str] = None

    # 5_Upscale
    upscale: Optional[bool] = False

    # Optional: Output path (kann automatisch generiert werden)
    output_path: Optional[str] = None

    # 2_LoRAs – Platzhalter für Erweiterungen
    loras: Optional[list] = []

    # 3_ControlNet – Platzhalter für Erweiterungen
    controlnet: Optional[dict] = {}

# 🧠 TOOL: TXT2IMG ENDPOINT
@app.post("/txt2img")
def txt2img_route(data: Txt2ImgRequest):
    return generate_image_from_json(data.dict())