# 🚀 FASTAPI SERVER – FÜR txt2img + img2vid

# 📦 IMPORTS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from img2vid_engine_wan import run_img2vid_wan
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os

# ✅ .env laden & BASE_URL setzen
load_dotenv("/workspace/.env")
BASE_URL = os.getenv("BASE_URL", "https://YOURPOD-8000.proxy.runpod.net")

# 🧠 IMPORTIERE TOOLS
from text2img import generate_image_from_json
from img2vid import generate_video_from_json

# 🚀 INITIALISIERE FASTAPI
app = FastAPI()

# 📂 DYNAMISCHER OUTPUT-PFAD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))                    # → /workspace/app
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../output"))       # → /workspace/output

# 🛠️ Debug-Ausgabe
print("📂 BASE_DIR:", BASE_DIR)
print("📂 OUTPUT_DIR:", OUTPUT_DIR)
if os.path.exists(OUTPUT_DIR):
    print("📁 OUTPUT-Dateien:", os.listdir(OUTPUT_DIR))
else:
    print("⚠️  OUTPUT-Ordner fehlt!")

# 📂 MOUNTE BILDAUSGABE
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

# 📄 DATENSTRUKTUR FÜR /txt2img
class Txt2ImgRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    model: str
    width: int
    height: int
    steps: int
    cfg: float
    sampler: str
    seed: Optional[int] = None
    upscale: Optional[bool] = False
    loras: Optional[list] = []
    controlnet: Optional[dict] = {}

# 🔁 TXT2IMG-ENDPOINT
@app.post("/txt2img")
async def txt2img_route(request: Txt2ImgRequest):
    output_path = generate_image_from_json(request.dict())
    filename = os.path.basename(output_path)
    return JSONResponse(content={"output_url": f"{BASE_URL}/output/{filename}"})

# 📄 DATENSTRUKTUR FÜR /img2vid WAN2.1
class Img2VidRequest(BaseModel):
    prompt: str
    image_url: str  # ⬅️ statt image_path
    fps: int = 12
    duration: int = 3  # Sekunden
    motion_strength: float = 1.0
    seed: Optional[int] = None
    model: str = "WAN2.1"
    loop: Optional[bool] = False
    interpolate: Optional[bool] = False
    camera_motion: Optional[str] = "none"
    output_path: Optional[str] = None

@app.post("/img2vid")
async def img2vid_route(request: Img2VidRequest):
    try:
        # Wandelt Request in Dict
        params = request.dict()

        # Übergibt an deine WAN2.1 Engine
        result = run_img2vid_wan(**params)

        # Fehler?
        if not result or result.get("status") != "✅ Success":
            return JSONResponse(status_code=500, content={
                "status": result.get("status", "❌ Failed"),
                "error": result.get("error", "Unbekannter Fehler in WAN2.1")
            })

        # ✅ Alles lief durch – Pfad zurückgeben
        output_path = result["output_path"]
        filename = os.path.basename(output_path)
        return {"output_url": f"{BASE_URL}/output/{filename}"}

    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "❌ Exception", "error": str(e)})


