import os
from datetime import datetime
from PIL import Image
from my_model_lib import load_model, run_inference

def generate_image_from_json(params: dict):
    try:
        # 📥 Eingabeparameter
        prompt = params["prompt"]
        model_name = params["model"]
        width = int(params["width"])
        height = int(params["height"])
        steps = int(params["steps"])
        cfg = float(params["cfg"])
        sampler = params["sampler"]
        seed = params.get("seed")
        upscale = bool(params.get("upscale", False))

        # 🧠 Modell laden & Bild generieren
        model = load_model(model_name)
        image = run_inference(
            model=model,
            prompt=prompt,
            negative_prompt=params.get("negative_prompt", ""),
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            sampler=sampler,
            seed=seed,
            loras=params.get("loras", []),
            controlnet=params.get("controlnet", {})
        )

        # 🔍 Optional Upscale
        if upscale:
            image = image.resize((width * 2, height * 2), Image.LANCZOS)

        # 📁 Speicherpfad dynamisch ermitteln
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))            # → /workspace/app
        OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "../output"))  # → /workspace/output
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"txt2img_{timestamp}.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        image.save(save_path)

        # 🌍 Rückgabe der URL (automatisch per ENV oder Default)
        pod_url = os.getenv("BASE_URL", "https://YOURPOD-8000.proxy.runpod.net")
        return f"{pod_url}/output/{filename}"

    except Exception as e:
        return f"❌ Error: {str(e)}"



