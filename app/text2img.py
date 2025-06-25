# 🧾 ZUTATEN & SETUP – alles was du für deine KI-Bildküche brauchst
import base64                      # ➜ Base64-Export fürs Web/API
from PIL import Image              # ➜ Bilder speichern & manipulieren
from io import BytesIO             # ➜ Bild als Bytestream für Base64
import uuid                        # ➜ Zufällige IDs für Seeds & Dateinamen
import os                          # ➜ Zugriff aufs Dateisystem
from datetime import datetime      # ➜ Zeitstempel für Dateinamen & Seeds
from diffusers import StableDiffusionPipeline  # ➜ Stable Diffusion Pipeline von HuggingFace
import torch                       # ➜ GPU-Berechnungen mit PyTorch

# 💾 Ausgabeordner für generierte Bilder
OUTPUT_FOLDER = "/home/jovyan/output/images/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 🧠 Modell-Mapping – weist jedem Alias den tatsächlichen Dateipfad zu
MODEL_MAP = {
    "absolutereality": "/home/jovyan/models/txt2img/absolutereality_v1.8.safetensors",
    "deliberate": "/home/jovyan/models/txt2img/deliberate_v3.safetensors",
    "dreamshaper": "/home/jovyan/models/txt2img/dreamshaper_8.safetensors",
    "epicrealism": "/home/jovyan/models/txt2img/epicrealism_v5.safetensors",
    "ghostmix": "/home/jovyan/models/txt2img/ghostmix_v2.5.safetensors",
    "photon": "/home/jovyan/models/txt2img/photon_v2.safetensors",
    "realvisxl": "/home/jovyan/models/txt2img/realvisxl_v1.5.safetensors",
    "toonyou": "/home/jovyan/models/txt2img/toonyou_v4.safetensors"
}

# 🚀 Hauptfunktion zur Generierung von Bildern aus einem JSON-Datensatz
def generate_image_from_json(data: dict):
    # 1️⃣ Standard-Einstellungen (Basisdaten)
    standard = data.get("1_Standard", {})
    model_key = standard.get("model", "absolutereality")                # 🧠 Modellname
    model_path = MODEL_MAP.get(model_key, model_key)                    # 📂 Modellpfad
    prompt = standard.get("prompt", "A futuristic city")               # 🎯 Prompt
    negative_prompt = standard.get("negative_prompt", "")              # ❌ Negative Prompt
    style = standard.get("style", "default")                           # 🎨 Stil
    mode = standard.get("mode", "quality")                             # ⚙️ Modus

    # ✅ Modellpfad prüfen
    if not os.path.isfile(model_path):
        raise ValueError(f"❌ Modellpfad existiert nicht: {model_path}")

    # 2️⃣ LoRA Einstellungen (noch nicht integriert)
    loras = data.get("2_LoRAs", [])                                     # 🔗 LoRAs (Platzhalter)

    # 3️⃣ ControlNet Daten (noch nicht integriert)
    control = data.get("3_ControlNet", {})                              # 🧩 ControlNet-Block
    control_type = control.get("type")                                  # 🔘 Typ
    control_image = control.get("input_image")                          # 🖼️ Bild
    control_weight = control.get("weight", 1.0)                         # ⚖️ Gewicht
    guidance_start = control.get("guidance_start", 0.0)                # 🕐 Startzeit
    guidance_end = control.get("guidance_end", 1.0)                    # 🕓 Endzeit

    # 4️⃣ Erweiterte Einstellungen
    adv = data.get("4_Advanced_Settings", {})
    width = adv.get("width", 832)                                       # 📐 Breite
    height = adv.get("height", 1242)                                    # 📏 Höhe
    steps = adv.get("steps", 30)                                        # 🔁 Schritte
    cfg = adv.get("cfg", 7)                                             # 🎚️ CFG Scale
    sampler = adv.get("sampler", "Euler")                              # 🔄 Sampler
    seed_str = adv.get("seed", f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:4]}")  # 🧬 Seed-String

    import hashlib
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16) % 2**32  # 🔢 Stabile Umrechnung

    # 5️⃣ Upscaler-Einstellungen
    upscaling = data.get("5_Upscale", {}).get("upscale", False)       # 🔍 Upscaling aktiv?

    # 🧪 Debug-Ausgabe
    print("🟢 Prompt:", prompt)
    print("🔴 Negative:", negative_prompt)
    print("📦 Model:", model_path, "| Style:", style, "| Mode:", mode)
    print("⚙️ Advanced:", width, height, steps, cfg, sampler, seed_str)

    # 🔁 Seed-Generator
    generator = torch.Generator(device="cuda").manual_seed(seed)

    # 🧠 Pipeline laden
    pipe = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float16
    ).to("cuda")

    # 🎨 Bild generieren
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        guidance_scale=cfg,
        num_inference_steps=steps,
        width=width,
        height=height,
        generator=generator
    ).images[0]

    # 💾 Speichern
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"img_{timestamp}.png"
    out_path = os.path.join(OUTPUT_FOLDER, filename)
    image.save(out_path)

    # 🔁 Base64 Rückgabe
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return {
        "filename": filename,
        "path": out_path,
        "base64": img_base64
    }

