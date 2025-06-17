# app/text2voice.py
import uuid, os

def generate(prompt: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/{uuid.uuid4().hex}.mp3"
    with open(path, "wb") as f:
        f.write(b"FAKE VOICE AUDIO FOR: " + prompt.encode())
    return path
