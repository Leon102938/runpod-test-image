# app/text2fsx.py
import uuid, os

def generate(prompt: str) -> str:
    os.makedirs("outputs", exist_ok=True)
    path = f"outputs/{uuid.uuid4().hex}.wav"
    with open(path, "wb") as f:
        f.write(b"FAKE SOUND FX FOR: " + prompt.encode())
    return path
