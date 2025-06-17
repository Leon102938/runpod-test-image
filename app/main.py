# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import FileResponse
import uuid, os

# 🔁 Importiere alle Tools
import text2img
import img2video
import text2music
import text2voice

app = FastAPI()

# 📥 Input-Schema
class PromptInput(BaseModel):
    prompt: str

# ✅ Gesundheits-Check
@app.get("/")
def root():
    return {"message": "KI Content API aktiv"}

# 🖼️ Text zu Bild
@app.post("/text2img")
def handle_text2img(data: PromptInput):
    try:
        path = text2img.generate(data.prompt)
        return FileResponse(path, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🎞️ Bild zu Video
@app.post("/img2video")
def handle_img2video(data: PromptInput):
    try:
        path = img2video.generate(data.prompt)
        return FileResponse(path, media_type="video/mp4")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🎵 Text zu Musik
@app.post("/text2music")
def handle_text2music(data: PromptInput):
    try:
        path = text2music.generate(data.prompt)
        return FileResponse(path, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🔊 Text zu Stimme
@app.post("/text2voice")
def handle_text2voice(data: PromptInput):
    try:
        path = text2voice.generate(data.prompt)
        return FileResponse(path, media_type="audio/mpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

