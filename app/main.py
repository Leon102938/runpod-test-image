# 🚀 FASTAPI SERVER – FÜR txt2img + img2vid

# 📦 IMPORTS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from wan_api import run_wan_ti2v
from pydantic import BaseModel
from typing import Optional
import os

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

@app.post("/wan/generate")
async def wan_generate(req: WanRequest):
    res = run_wan_ti2v(
        prompt=req.prompt,
        size=req.size,
        frame_num=req.frame_num,
        sample_steps=req.sample_steps,
        sample_guide_scale=req.sample_guide_scale,
        offload_model=req.offload_model,
        convert_model_dtype=req.convert_model_dtype,
        task=req.task,
    )
    # Wenn BASE_URL aus start.sh gesetzt ist, liefern wir eine Log-URL zurück
    base_url = os.getenv("BASE_URL", "")
    log_url = f"{base_url}/output/../logs/{os.path.basename(res['log'])}" if base_url else ""
    return {"ok": True, "run": res, "log_url": log_url}






