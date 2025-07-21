# 📦 IMPORTS & GRUNDLAGEN
import os
from datetime import datetime
import json

# 🧠 Dein echter Motor
from img2vid_engine import load_video_model, run_video_inference

# 🎥 Hauptfunktion: Bild → Video (und optional Text → Video)
def generate_video_from_json(params: dict):
    try:
        if not params:
            raise ValueError("⛔ Keine Parameter erhalten (params ist None oder leer)")

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

        # ✅ Eingabeparameter mit Schutz + Defaults
        prompt = params.get("prompt", "")
        if not prompt:
            raise ValueError("⛔ Prompt fehlt!")

        negative_prompt = params.get("negative_prompt", "")
        image_path = params.get("image_path", None)  # ← optional für txt2vid!
        model_name = params.get("model")
        if not model_name:
            raise ValueError("⛔ Model-Name fehlt!")

        fps = int(params.get("fps", 16))
        duration = int(params.get("duration", 4))
        motion_strength = float(params.get("motion_strength", 1.2))
        seed = params.get("seed", None)
        loop = bool(params.get("loop", False))
        interpolate = bool(params.get("interpolate", False))
        camera_motion = params.get("camera_motion", "none")

        # 🔧 Modellpfad zusammensetzen
        model_dir = "/workspace/ai-core/models/IMG2Vid"
        model_path = os.path.join(model_dir, model_name)

        # 🧠 Modell laden
        model = load_video_model(model_path)

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
        print(f"❌ EXCEPTION: {str(e)}")
        return {"status": "❌ Failed", "error": str(e)}
