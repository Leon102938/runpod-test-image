# 🚀 FASTAPI SERVER – SORTIERT NACH MODELLGRUPPEN

# 📦 FASTAPI: Hauptserver für alle KI-Tools

from fastapi import FastAPI, Request
from pydantic import BaseModel

# 📸 Bild/Video Tools – direkte Imports aus dem gleichen Verzeichnis
from text2img import generate_image_from_json
from img2vid import generate_video
from text2vid import generate_video_from_text

# 🔊 Audio/Text Tools
from text2musik import generate_music
from text2voice import generate_voice
from text2fsx import generate_fsx

# 🌐 Starte FastAPI
app = FastAPI()

# 🧩 Gemeinsame Input-Datenstruktur für alle Tools
class Input(BaseModel):
    prompt: str
    style: str = "default"

# 🖼️ TEXT-TO-IMAGE
@app.post("/txt2img")
async def txt2img_route(request: Request):
    data = await request.json()
    image_path = generate_image_from_json(data)
    return {"output": image_path}

# 🎞️ IMAGE-TO-VIDEO
@app.post("/img2vid")
def img2vid_route(data: Input):
    return {"output": generate_video(data.prompt, data.style)}

# 📽️ TEXT-TO-VIDEO
@app.post("/text2vid")
def text2vid_route(data: Input):
    return {"output": generate_video_from_text(data.prompt, data.style)}

# 🎵 TEXT-TO-MUSIC
@app.post("/text2musik")
def text2musik_route(data: Input):
    return {"output": generate_music(data.prompt, data.style)}

# 🗣️ TEXT-TO-VOICE
@app.post("/text2voice")
def text2voice_route(data: Input):
    return {"output": generate_voice(data.prompt, data.style)}

# 🧠 TEXT-TO-FSX (z. B. Effekte)
@app.post("/text2fsx")
def text2fsx_route(data: Input):
    return {"output": generate_fsx(data.prompt, data.style)}

