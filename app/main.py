# 🚀 FASTAPI SERVER – FÜR txt2img + img2vid + opensora

# 📦 IMPORTS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional
import os
import io
import base64
import imageio

# ✅ .env laden & BASE_URL setzen
load_dotenv("/workspace/.env")
BASE_URL = os.getenv("BASE_URL", "https://YOURPOD-8000.proxy.runpod.net")

# 🧠 IMPORTIERE TOOLS
from text2img import generate_image_from_json
from img2vid import generate_video_from_json

# 🧠 OpenSora Engine importieren
from app.open_sora_engine import OpenSoraEngine

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


# 📄 DATENSTRUKTUR FÜR /img2vid
class Img2VidRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = ""
    image_path: str
    fps: int
    duration: int
    motion_strength: float
    seed: Optional[int] = None
    model: str
    loop: Optional[bool] = False
    interpolate: Optional[bool] = False
    camera_motion: Optional[str] = "none"
    output_path: Optional[str] = None

@app.post("/img2vid")
async def img2vid_route(request: Img2VidRequest):
    result = generate_video_from_json(request.dict())

    # 🛑 Fehlerbehandlung
    if not result or result.get("status") != "✅ Success":
        return JSONResponse(status_code=500, content={
            "status": result.get("status", "❌ Failed"),
            "error": result.get("error", "Unbekannter Fehler im img2vid_endpoint")
        })

    # ✅ Erfolgreich
    output_path = result["output_path"]
    filename = os.path.basename(output_path)
    return {"output_url": f"{BASE_URL}/output/{filename}"}


# 📄 DATENSTRUKTUR FÜR /opensora
class OpenSoraRequest(BaseModel):
    prompt: str

# 🧠 Engine initialisieren (nur einmal beim Start)
opensora_engine = OpenSoraEngine(
    model_path="/workspace/models/text2Video/OpenSora/Open_Sora_v2.safetensors",
    vae_path="/workspace/models/text2Video/OpenSora/hunyuan_vae.safetensors"
)
opensora_engine.load_model()

# 🔁 OPENSORA-ENDPOINT
@app.post("/opensora")
async def opensora_route(request: OpenSoraRequest):
    try:
        video_tensor = opensora_engine.generate(prompt=request.prompt)

        # Als GIF kodieren (Vorschau)
        buffer = io.BytesIO()
        imageio.mimsave(buffer, video_tensor[0], format="GIF", fps=8)
        encoded_gif = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "status": "✅ Success",
            "video_base64_gif": encoded_gif
        }

    except Exception as e:
        return {
            "status": "❌ Failed",
            "error": str(e)
        }





