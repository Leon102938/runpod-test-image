#!/usr/bin/python3

import os
import torch
from torchvision.utils import save_image
from PIL import Image
import imageio
from safetensors.torch import load_file
from diffusers import AutoencoderKL, UNet2DConditionModel, DDIMScheduler
from transformers import T5Tokenizer, T5EncoderModel
import argparse
import json

# ----------- CONFIG -----------
MODEL_DIR = "/workspace/app/models"
OUTPUT_FRAMES_DIR = "frames"
VAE_PATH = os.path.join(MODEL_DIR, "Wan2.1_VAE.pth")
UNET_WEIGHTS_PATH = os.path.join(MODEL_DIR, "diffusion_pytorch_model.safetensors")
UNET_CONFIG_PATH = os.path.join(MODEL_DIR, "config.json")
TEXT_ENCODER_NAME = "google/umt5-base"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ----------- TEXT ENCODING -----------
def load_text_embedding(prompt):
    print(f"[INFO] Loading T5 tokenizer & encoder: {TEXT_ENCODER_NAME}")
    tokenizer = T5Tokenizer.from_pretrained(TEXT_ENCODER_NAME)
    encoder = T5EncoderModel.from_pretrained(TEXT_ENCODER_NAME).to(DEVICE)
    tokens = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).input_ids.to(DEVICE)
    with torch.no_grad():
        embedding = encoder(input_ids=tokens).last_hidden_state
    print(f"[DEBUG] Text embedding shape: {embedding.shape}")
    if torch.isnan(embedding).any():
        raise ValueError("Embedding contains NaNs. TextEncoder failed.")
    return embedding

# ----------- SAVE VIDEO -----------
def save_frames_to_video(frame_dir, output_path, fps=8):
    frames = sorted([os.path.join(frame_dir, f) for f in os.listdir(frame_dir) if f.endswith(".png")])
    imgs = [imageio.v2.imread(f) for f in frames]
    imageio.mimsave(output_path, imgs, fps=fps)
    print(f"[INFO] Saved video to {output_path}")

# ----------- MAIN FUNCTION -----------
def generate_video(prompt, output_path="output.mp4", num_frames=16):
    os.makedirs(OUTPUT_FRAMES_DIR, exist_ok=True)
    print(f"[INFO] Prompt: '{prompt}'")
    text_emb = load_text_embedding(prompt)

    print("[INFO] Loading VAE & UNet...")

    # Load VAE
    vae = torch.load(VAE_PATH, map_location=DEVICE)

    # Load UNet config from local file
    with open(UNET_CONFIG_PATH, "r") as f:
        unet_config = json.load(f)
    unet = UNet2DConditionModel.from_config(unet_config).to(DEVICE)
    unet.load_state_dict(load_file(UNET_WEIGHTS_PATH))

    # Load DDIM Scheduler
    scheduler = DDIMScheduler.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="scheduler")
    scheduler.set_timesteps(25)

    for i in range(num_frames):
        latents = torch.randn((1, 4, 64, 64)).to(DEVICE)
        for t in scheduler.timesteps:
            with torch.no_grad():
                noise_pred = unet(latents, t, encoder_hidden_states=text_emb).sample
            latents = scheduler.step(noise_pred, t, latents).prev_sample

        with torch.no_grad():
            image = vae.decode(latents).sample
        save_image(image[0], f"{OUTPUT_FRAMES_DIR}/frame_{i:03d}.png")

    save_frames_to_video(OUTPUT_FRAMES_DIR, output_path)

# ----------- CLI -----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--output", type=str, default="output.mp4")
    parser.add_argument("--frames", type=int, default=16)
    args = parser.parse_args()

    generate_video(args.prompt, args.output, args.frames)
