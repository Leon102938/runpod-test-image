# my_model_lib.py

from diffusers import StableDiffusionPipeline
import torch
import os

# Modellpfade (Name = Dateiname ohne .safetensors)
MODEL_PATHS = {
    "absolutereality": "/workspace/ai-core/models/txt2img/absolutereality_v1.8.safetensors",
    "deliberate": "/workspace/ai-core/models/txt2img/deliberate_xl.safetensors",
    "dreamshaper": "/workspace/ai-core/models/txt2img/dreamshaper_8.safetensors",
    "epicrealism": "/workspace/ai-core/models/txt2img/epicrealism_v6.5.safetensors",
    "ghostmix": "/workspace/ai-core/models/txt2img/ghostmix_v2.safetensors",
    "photon": "/workspace/ai-core/models/txt2img/photon_v2.safetensors",
    "realvisxl": "/workspace/ai-core/models/txt2img/realvisxl_v5.safetensors",
    "toonyou": "/workspace/ai-core/models/txt2img/toonyou_v4.safetensors"
}

# Cache für geladene Modelle
loaded_models = {}

def load_model(name: str):
    if name in loaded_models:
        return loaded_models[name]

    model_path = MODEL_PATHS.get(name)
    if not model_path or not os.path.exists(model_path):
        raise ValueError(f"❌ Modellpfad ungültig oder fehlt: {name}")

    print(f"🚀 Lade Modell: {model_path}")

    pipe = StableDiffusionPipeline.from_single_file(
        model_path,
        torch_dtype=torch.float16,
        safety_checker=None
    ).to("cuda")

    pipe.enable_attention_slicing()

    loaded_models[name] = pipe
    return pipe

def run_inference(model, prompt, negative_prompt, width, height, steps, cfg, sampler, seed, loras, controlnet):
    generator = torch.manual_seed(seed) if seed else None

    result = model(
        prompt=prompt,
        negative_prompt=negative_prompt,
        width=width,
        height=height,
        num_inference_steps=steps,
        guidance_scale=cfg,
        generator=generator
    )

    image = result.images[0]
    return image
