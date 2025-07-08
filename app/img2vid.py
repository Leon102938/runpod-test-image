# 📦 IMPORTS & GRUNDLAGEN
import os
from datetime import datetime
import json

# 🧠 Dein echter Motor (muss angepasst werden auf dein reales Backend!)
from img2vid_engine import load_video_model, run_video_inference

# 🎥 Hauptfunktion: Bild → Video
def generate_video_from_json(params: dict):
    try:
        # 📋 LOGGING (Debug-Ausgabe + Speicherung)
        print("\n" + "="*60)
        print(f"📅 VIDEO GENERATION TIMESTAMP: {datetime.now().isoformat()}")
        print("🎥 INFERENCE CONFIGURATION:")
        print(json.dumps(params, indent=4))
        print("="*60 + "\n")

        try:
            os.makedirs("/workspace/logs", exist_ok=True)
            with open("/workspace/logs/video_inference.log", "a") as f:
                f.write(f"\n[{datetime.now().isoformat()}] Video Inference:\n")
                f.write(json.dumps(params, indent=4) + "\n")
        except Exception as log_error:
            print(f"⚠️ Video Logging failed: {log_error}")

        # 📥 Eingabeparameter (ohne Fallbacks)
        prompt = params["prompt"]
        negative_prompt = params.get("negative_prompt", "")
        image_path = params["image_path"]
        model_name = params["model"]
        fps = int(params["fps"])
        duration = int(params["duration"])
        motion_strength = float(params["motion_strength"])
        seed = params.get("seed", None)
        loop = bool(params.get("loop", False))
        interpolate = bool(params.get("interpolate", False))
        camera_motion = params.get("camera_motion", "none")

        # 🧠 Modellpfad anpassen (nur Dateiname → ganzer Pfad)
        if not os.path.isabs(model_name):
            model_name = os.path.join("/workspace/ai-core/models/IMG2Vid", model_name)

        # 🧠 Modell laden
        model = load_video_model(model_name)

        # 🎬 Video generieren
        video = run_video_inference(
            model=model,
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            fps=fps,
            duration=duration,
            motion_strength=motion_strength,
            seed=seed,
            loop=loop,
            interpolate=interpolate,
            camera_motion=camera_motion
        )

        # 💾 Output automatisch erzeugen & speichern
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/workspace/output/img2vid_{timestamp}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "wb") as f:
            f.write(video)

        return {"status": "✅ Success", "output_path": output_path}

    except Exception as e:
        return {"status": "❌ Failed", "error": str(e)}
