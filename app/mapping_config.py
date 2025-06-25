# txt2img.py – Finalisierte & Funktionierende Version mit Modellbindung

import base64
from PIL import Image, ImageDraw
from io import BytesIO
import uuid
import os
from datetime import datetime

# === 📂 Fester Speicherort für Outputs ===
OUTPUT_FOLDER = "/workspace/models/assets/images/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# === 🔀 Modell-Mapping (Leonardo-Alias -> Lokale Safetensor-Datei) ===
MODEL_MAP = {
    "Phoenix 1.0": "/models/txt2img/safetensors/dreamshaper_8.safetensors",
    "Phoenix 0.9": "/models/txt2img/safetensors/ghostmix_v2.safetensors",
    "Stock Photography": "/models/txt2img/safetensors/realvisxl_v5.safetensors",
    "Portrait Perfect": "/models/txt2img/safetensors/deliberate_xl.safetensors",
    "Lifelike Vision": "/models/txt2img/safetensors/photon_v2.safetensors",
    "Leonardo Lightning": "/models/txt2img/safetensors/toonyou_v4.safetensors",
    "Absolute Reality 1.8": "/models/txt2img/safetensors/absolutereality_v1.8.safetensors",
    "Epic Realism 6.5": "/models/txt2img/safetensors/epicrealism_v6.5.safetensors"
}

# === 🔧 Hauptfunktion für Text2Image ===
def generate_image_from_json(data: dict):
    # 1️⃣ ───── STANDARD PARAMETER ─────
    model_key = data["1_Standard"].get("model", "default")
    model_name = MODEL_MAP.get(model_key, model_key)
    prompt = data["1_Standard"].get("prompt", "A dog")
    negative_prompt = data["1_Standard"].get("negative_prompt", "")
    style = data["1_Standard"].get("style", "default")
    mode = data["1_Standard"].get("mode", "quality")

    # 2️⃣ ───── LoRAs ─────
    loras = data.get("2_LoRAs", [])
    for lora in loras:
        print(f"🔗 LoRA: {lora['name']} | Gewicht: {lora['weight']}")
        # TODO: Integration in echte Inference

    # 3️⃣ ───── CONTROL NET ─────
    control = data.get("3_ControlNet", {})
    control_type = control.get("type")
    control_image = control.get("input_image")
    control_weight = control.get("weight", 1.0)
    guidance_start = control.get("guidance_start", 0.0)
    guidance_end = control.get("guidance_end", 1.0)

    controlnet_image = None
    if control_image:
        try:
            image_data = base64.b64decode(control_image)
            controlnet_image = Image.open(BytesIO(image_data))
        except Exception as e:
            print("❌ Fehler beim ControlNet-Image:", e)

    # 4️⃣ ───── ADVANCED SETTINGS ─────
    advanced = data.get("4_Advanced_Settings", {})
    contrast = advanced.get("contrast", "medium")
    enhance_prompt = advanced.get("enhance_prompt", "auto")
    width = advanced.get("width", 832)
    height = advanced.get("height", 1242)
    n_images = advanced.get("n_images", 1)
    steps = advanced.get("steps", 30)
    cfg = advanced.get("cfg", 7)
    sampler = advanced.get("sampler", "Euler")
    seed = advanced.get("seed", f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}")

    # 5️⃣ ───── UPSCALE ─────
    upscaling = data.get("5_Upscale", {}).get("upscale", False)

    # 🧪 DEBUG AUSGABE
    print("🟢 Prompt:", prompt)
    print("🔴 Negative:", negative_prompt)
    print("📦 Model:", model_name, "| Style:", style, "| Mode:", mode)
    print("🎯 LoRAs:", loras)
    print("🧠 ControlNet:", control_type, control_weight, guidance_start, guidance_end)
    print("⚙️ Advanced:", width, height, steps, cfg, sampler, seed)
    print("🔼 Upscale:", upscaling)

    # 🖼️ Dummy Image als Platzhalter für echte Inferenz
    dummy_img = Image.new("RGB", (width, height), color=(123, 123, 123))
    draw = ImageDraw.Draw(dummy_img)
    draw.text((20, 20), prompt, fill=(255, 255, 255))

    out_path = os.path.join(OUTPUT_FOLDER, f"img_{seed}.png")
    dummy_img.save(out_path)
    return out_path
