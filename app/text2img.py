# 📦 IMPORTS & GRUNDLAGEN
import os
from datetime import datetime
from PIL import Image

# z. B. diffusers, comfyui oder invokeai
# Bei dir vermutlich: stable-diffusion-webui oder ein anderer Loader
# Hier wird angenommen, dass dein Backend in "my_model_lib" liegt

# ⬇️ Beispielhaft – du ersetzt dies mit deiner echten Model-Logik
from my_model_lib import load_model, run_inference

# 📂 MODELLE LADEN (je nach Model-Name)
MODEL_PATHS = {
    "absolutereality": "/workspace/ai-core/models/txt2img/absolutereality_v1.8.safetensors",
    "deliberate": "/workspace/ai-core/models/txt2img/deliberate.safetensors",
    "epicrealism": "/workspace/ai-core/models/txt2img/epicrealism_v6.safetensors"
}

loaded_models = {}

def get_model(name):
    if name in loaded_models:
        return loaded_models[name]
    path = MODEL_PATHS.get(name)
    if not path or not os.path.exists(path):
        raise ValueError(f"❌ Modell '{name}' nicht gefunden oder Pfad ungültig!")
    model = load_model(path)
    loaded_models[name] = model
    return model

# 📸 BILD GENERIERUNG

def generate_image_from_json(params):
    prompt = params.get("prompt")
    negative_prompt = params.get("negative_prompt", "")
    model_name = params.get("model", "absolutereality")
    width = params.get("width", 832)
    height = params.get("height", 1242)
    steps = params.get("steps", 30)
    cfg = params.get("cfg", 7.0)
    sampler = params.get("sampler", "Euler")
    seed = params.get("seed", None)
    upscale = params.get("upscale", False)
    output_path = params.get("output_path")
    loras = params.get("loras", [])
    controlnet = params.get("controlnet", {})

    # 📦 Modell laden
    model = get_model(model_name)

    # 🧠 Bild generieren
    image = run_inference(
        model=model,
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        steps=steps,
        cfg=cfg,
        sampler=sampler,
        seed=seed,
        loras=loras,
        controlnet=controlnet
    )

    # 🖼️ Upscale optional
    if upscale:
        image = image.resize((width*2, height*2), Image.LANCZOS)

    # 📁 Output-Ordner + Auto-Filename
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/workspace/output/txt2img_{timestamp}.png"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    image.save(output_path)

    return {"status": "✅ Success", "output_path": output_path}

