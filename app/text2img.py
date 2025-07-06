import os
from datetime import datetime
from PIL import Image
import json

from my_model_lib import load_model, run_inference

def generate_image_from_json(params: dict):
    try:
        # Eingaben
        prompt = params["prompt"]
        model_name = params["model"]
        width = int(params["width"])
        height = int(params["height"])
        steps = int(params["steps"])
        cfg = float(params["cfg"])
        sampler = params["sampler"]
        seed = params.get("seed")
        upscale = bool(params.get("upscale", False))

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

        if upscale:
            image = image.resize((width * 2, height * 2), Image.LANCZOS)

        # Speicherpfad (automatisch)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"txt2img_{timestamp}.png"
        output_path = f"/workspace/output/{filename}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)

        # Nur URL zurückgeben
        pod_url = os.getenv("BASE_URL", "https://YOURPOD-8000.proxy.runpod.net")
        return f"{pod_url}/output/{filename}"

    except Exception as e:
        return f"❌ Error: {str(e)}"



