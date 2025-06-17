# app/img2vid.py
from moviepy.editor import ImageClip
import os, uuid

def generate(image_path: str) -> str:
    clip = ImageClip(image_path).set_duration(5)
    clip = clip.set_fps(24)

    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/{uuid.uuid4().hex}.mp4"
    clip.write_videofile(path)
    return path

