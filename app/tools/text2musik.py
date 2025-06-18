# 🎼 TEXT2MUSIK
import uuid

def generate_music(prompt: str, style: str) -> str:
    output_path = f"/workspace/generated/{uuid.uuid4().hex}.mp3"
    with open(output_path, "w") as f:
        f.write("Dummy Music")
    return output_path

