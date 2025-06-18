# 🗣️ TEXT2VOICE
import uuid

def generate_voice(prompt: str, style: str) -> str:
    output_path = f"/workspace/generated/{uuid.uuid4().hex}.wav"
    with open(output_path, "w") as f:
        f.write("Dummy Voice")
    return output_path

