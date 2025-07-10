# img2vid_engine.py

import torch
from diffusers import AnimateDiffPipeline
from urllib.request import urlopen
from PIL import Image
import numpy as np
import random
import tempfile
import imageio
import os

# 🔁 Modell laden
def load_video_model(model_name: str):
    model_path = model_name
    pipe = AnimateDiffPipeline.from_pretrained(
        model_path,
        torch_dtype=torch.float16
    ).to("cuda")
    pipe.enable_model_cpu_offload()
    pipe.enable_vae_tiling()
    pipe.enable_attention_slicing()
    return pipe


# 🧠 Videogenerierung
def run_video_inference(
    model,
    image_path,
    prompt,
    negative_prompt,
    fps,
    duration,
    motion_strength,
    seed=None,
    loop=False,
    interpolate=False,
    camera_motion="none"
):
    # 🧪 Seed setzen
    if seed is not None:
        generator = torch.manual_seed(seed)
    else:
        generator = torch.manual_seed(random.randint(0, 999999))

    # 🖼️ Bild vorbereiten (lokal oder URL)
    if image_path.startswith("http://") or image_path.startswith("https://"):
        image = Image.open(urlopen(image_path)).convert("RGB")
    else:
        image = Image.open(image_path).convert("RGB")

    image = image.resize((512, 512))  # Modelltypisch
    image_tensor = torch.tensor(np.array(image)).permute(2, 0, 1).float() / 255.0
    image_tensor = image_tensor.unsqueeze(0).to("cuda")

    # 🎥 Anzahl Frames
    num_frames = int(fps * duration)

    # 🔁 Generieren
    with torch.no_grad():
        output = model(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image_tensor,
            num_frames=num_frames,
            guidance_scale=motion_strength,
            generator=generator
        )

    # 🔁 Optional: Interpolation (Future Implementation – Placeholder)
    if interpolate:
        print("🌀 Interpolation requested – not implemented in this version.")

    # 🔁 Optional: Camera-Motion (Placeholder Logic)
    if camera_motion != "none":
        print(f"📷 Camera Motion: {camera_motion} (not implemented yet)")

    # 🎞️ MP4-Speicherung
    frames = output.frames[0].cpu().permute(0, 2, 3, 1).numpy()
    frames = (frames * 255).astype(np.uint8)

    temp_path = tempfile.mktemp(suffix=".mp4")
    imageio.mimsave(temp_path, frames, fps=fps)

    # 🔁 Optional: Loop (z. B. Frames rückwärts anhängen)
    if loop:
        print("🔁 Loop requested – not implemented yet.")

    # ✅ Pfad zum MP4-Video zurückgeben
    with open(temp_path, "rb") as f:
        video_bytes = f.read()

    return video_bytes
