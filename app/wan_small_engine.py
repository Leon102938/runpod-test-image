#!/usr/bin/env python3

import os
import torch
import argparse
import imageio
from torchvision.utils import save_image
from transformers import T5Tokenizer, T5EncoderModel
from diffusers import UNet2DConditionModel, DDIMScheduler, AutoencoderKL

# -------- CONFIG --------
MODEL_DIR = "/workspace/models/wan2.1"
OUTPUT_FRAMES_DIR = "frames"
TOKENIZER_NAME = "t5-base"  # oder "google/umt5-xxl" wenn GPU & RAM passen
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# -------- LOADERS --------
def load_text_embedding(prompt):
    print("[INFO] Loading tokenizer & encoder...")
    tokenizer = T5Tokenizer.from_pretrained(TOKENIZER_NAME)
    encoder = T5EncoderModel.from_pretrained(TOKENIZER_NAME).to(DEVICE).eval()
    tokens = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).input_ids.to(DEVICE)
    with torch.no_grad():
        embedding = encoder(input_ids=tokens).last_hidden_state
    print(f"[DEBUG] Text embedding shape: {embedding.shape}")
    return embedding

def load_unet():
    print("[INFO] Loading UNet from", MODEL_DIR)
    return UNet2DConditionModel.from_pretrained(
        MODEL_DIR,
        use_safetensors=True
    ).to(DEVICE).eval()

def load_vae():
    print("[INFO] Loading VAE from", MODEL_DIR)
    return AutoencoderKL.from_pretrained(
        MODEL_DIR,
        subfolder="vae"
    ).to(DEVICE).eval()

def save_frames_to_video(frame_dir, output_path, fps=8):
    print("[INFO] Saving frames to video...")
    frames = sorted([f for f in os.listdir(frame_dir) if f.endswith(".png")])
    images = [imageio.v2.imread(os.path.join(frame_dir, f)) for f in frames]
    imageio.mimsave(output_path, images, fps=fps)
    print(f"[INFO] Video saved: {output_path}")

# -------- MAIN --------
def generate_video(prompt, output_path="output.mp4", num_frames=16):
    os.makedirs(OUTPUT_FRAMES_DIR, exist_ok=True)
    print(f"[INFO] Generating video for prompt: '{prompt}'")

    text_emb = load_text_embedding(prompt)
    unet = load_unet()
    vae = load_vae()
    scheduler = DDIMScheduler.from_pretrained("CompVis/stable-diffusion-v1-4", subfolder="scheduler")
    scheduler.set_timesteps(25)

    for i in range(num_frames):
        latents = torch.randn((1, 4, 64, 64)).to(DEVICE)
        for t in scheduler.timesteps:
            with torch.no_grad():
                noise_pred = unet(
                    sample=latents,
                    timestep=t,
                    encoder_hidden_states=text_emb
                ).sample
            latents = scheduler.step(noise_pred, t, latents).prev_sample

        with torch.no_grad():
            image = vae.decode(latents).sample
        save_image(image[0], f"{OUTPUT_FRAMES_DIR}/frame_{i:03d}.png")

    save_frames_to_video(OUTPUT_FRAMES_DIR, output_path)

# -------- CLI --------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", type=str, required=True, help="Prompt text")
    parser.add_argument("--output", type=str, default="output.mp4", help="Output video filename")
    parser.add_argument("--frames", type=int, default=16, help="Number of frames to generate")
    args = parser.parse_args()

    generate_video(args.prompt, args.output, args.frames)
