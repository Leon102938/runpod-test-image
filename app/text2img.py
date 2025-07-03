# 📦 IMPORTS & GRUNDLAGEN
import os
from datetime import datetime
from PIL import Image
import json

# 🧠 Dein echter Motor
from my_model_lib import load_model, run_inference

# 🖼️ Hauptfunktion: Prompt → Bild
def generate_image_from_json(params: dict):
    try:
        # 📋 LOGGING (Debug-Ausgabe + Speicherung)
        print("\n" + "="*60)
        print(f"📅 GENERATION TIMESTAMP: {datetime.now().isoformat()}")
        print("🚀 INFERENCE CONFIGURATION:")
        print(json.dumps(params, indent=4))
        print("="*60 + "\n")

        try:
            os.makedirs("/workspace/logs", exist_ok=True)
            with open("/workspace/logs/inference.log", "a") as f:
                f.write(f"\n[{datetime.now().isoformat()}] Inference:\n")
                f.write(json.dumps(params, indent=4) + "\n")
        except Exception as log_error:
            print(f"⚠️ Logging failed: {log_error}")

        # 📥 Eingabeparameter ohne Fallbacks
        prompt = params["prompt"]
        negative_prompt = params.get("negative_prompt", "")
        model_name = params["model"]
        width = int(params["width"])
        height = int(params["height"])
        steps = int(params["steps"])
        cfg = float(params["cfg"])
        sampler = params["sampler"]
        seed = params.get("seed", None)
        upscale = bool(params.get("upscale", False))
        output_path = params.get("output_path")

        loras = params.get("loras", [])
        if not isinstance(loras, list):
            loras = []

        controlnet = params.get("controlnet", {})
        if not isinstance(controlnet, dict):
            controlnet = {}

        # 📦 Modell laden
        model = load_model(model_name)

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

        # 🆙 Upscaling (nur wenn explizit true)
        if upscale:
            image = image.resize((width * 2, height * 2), Image.LANCZOS)

        # 💾 Output speichern
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"/workspace/output/txt2img_{timestamp}.png"

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)

        # 🌐 Output-URL zusätzlich zurückgeben
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        rel_path = os.path.relpath(output_path, start=".")
        url = f"{base_url}/{rel_path}"

        return {
            "status": "✅ Success",
            "output_path": output_path,
            "output_url": url
        }

    except Exception as e:
        return {"status": "❌ Failed", "error": str(e)}


