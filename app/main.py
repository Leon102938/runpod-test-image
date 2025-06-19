# 🚀 FASTAPI SERVER – SORTIERT NACH MODELLGRUPPEN

from fastapi import FastAPI
from pydantic import BaseModel

# 📸 Bild/Video Tools – direkte Imports aus dem gleichen Verzeichnis
from text2img import generate_image
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
def txt2img_route(data: Input):
    return {"output": generate_image(data.prompt, data.style)}

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

