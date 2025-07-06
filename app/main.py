# 🚀 FASTAPI SERVER – FÜR txt2img + img2vid

# 📦 IMPORTS
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

# 🧠 IMPORTIERE TOOLS
from text2img import generate_image_from_json
from img2vid import generate_video_from_json

# 🚀 INITIALISIERE FASTAPI
app = FastAPI()

# 📂 MOUNTE BILDAUSGABE
os.makedirs("/workspace/output", exist_ok=True)
app.mount("/output", StaticFiles(directory="/workspace/output"), name="output")

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
    url = generate_image_from_json(request.dict())
    return JSONResponse(content={"output_url": url})

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

# 🔁 IMG2VID-ENDPOINT
@app.post("/img2vid")
async def img2vid_route(request: Img2VidRequest):
    video_path = generate_video_from_json(request.dict())
    return {"output": video_path}



