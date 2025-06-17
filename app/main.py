# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import uuid, os
from PIL import Image, ImageDraw
import text2img, img2video, text2music, text2voice

app = FastAPI()

class PromptInput(BaseModel):
    prompt: str

@app.get("/")
def root():
    return {"message": "KI Content API aktiv"}

@app.post("/text2img")
def handle_text2img(data: PromptInput):
    path = text2img.generate(data.prompt)
    return FileResponse(path, media_type="image/png")

@app.post("/img2video")
def handle_img2video(data: PromptInput):
    path = img2video.generate(data.prompt)
    return FileResponse(path, media_type="video/mp4")

@app.post("/text2music")
def handle_text2music(data: PromptInput):
    path = text2music.generate(data.prompt)
    return FileResponse(path, media_type="audio/mpeg")

@app.post("/text2voice")
def handle_text2voice(data: PromptInput):
    path = text2voice.generate(data.prompt)
    return FileResponse(path, media_type="audio/mpeg")

