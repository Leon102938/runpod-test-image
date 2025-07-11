import torch
from diffusers import DiffusionPipeline
from pathlib import Path
from PIL import Image
import imageio
import os
import uuid
import requests
from io import BytesIO

# 📂 Modellpfad
WAN2_MODEL_PATH = "/workspace/ai-core/models/IMG2VID/WAN2.1"
OUTPUT_DIR = "/workspace/output"

# ✅ Modell laden
pipe = DiffusionPipeline.from_pretrained(
    WAN2_MODEL_PATH,
    torch_dtype=torch.float16,
    use_safetensors=True,
).to("cuda")

# 🎥 Bildsequenz → MP4 speichern
def save_video(frames, output_path, fps=12):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with imageio.get_writer(output_path, fps=fps) as writer:
        for frame in frames:
            if isinstance(frame, Image.Image):
                writer.append_data(imageio.v3.asarray(frame.convert("RGB")))

# 🚀 Hauptfunktion
def run_img2vid_wan(
    prompt: str,
    image_url: str = "",
    fps: int = 12,
    duration: int = 3,
    motion_strength: float = 1.0,
    seed: int = None,
    model: str = "WAN2.1",
    loop: bool = False,
    interpolate: bool = False,
    camera_motion: str = "none",
    output_path: str = None
):
    try:
        num_frames = duration * fps

        # ✅ Seed (optional)
        if seed is not None:
            torch.manual_seed(seed)

        # 🖼️ Bild von URL laden
        if not image_url:
            raise ValueError("image_url is required")

        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content)).convert("RGB")

        # 🔮 Inferenz mit Bild & Prompt
        result = pipe(
            prompt=prompt,
            image=image,
            num_frames=num_frames,
            guidance_scale=motion_strength,
        )

        # 🎞️ Speichern
        video_id = uuid.uuid4().hex[:8]
        final_path = output_path or f"{OUTPUT_DIR}/img2vid_{video_id}.mp4"
        save_video(result.frames, final_path, fps=fps)

        return {
            "status": "✅ Success",
            "output_path": final_path
        }

    except Exception as e:
        return {
            "status": "❌ Failed",
            "error": str(e)
        }

