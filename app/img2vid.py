# 🎞️ IMG2VID
import uuid

def generate_video(prompt: str, style: str) -> str:
    output_path = f"/workspace/generated/{uuid.uuid4().hex}.mp4"
    with open(output_path, "w") as f:
        f.write("Dummy video")
    return output_path


