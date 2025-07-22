import torch
from pathlib import Path
from diffusers.models import AutoencoderKLTemporalDecoder
from diffusers.pipelines import StableVideoDiffusionPipeline
from safetensors.torch import load_file
from typing import Optional
import os

class OpenSoraEngine:
    def __init__(self, model_path: str, vae_path: Optional[str] = None):
        self.model_path = model_path
        self.vae_path = vae_path
        self.pipe = None

    def load_model(self):
        print("🔄 Lade OpenSora-Modell...")

        # 🔧 VAE laden, wenn vorhanden
        vae = None
        if self.vae_path and os.path.exists(self.vae_path):
            print(f"📦 Lade VAE: {self.vae_path}")
            vae = AutoencoderKLTemporalDecoder.from_pretrained(
                self.vae_path,
                torch_dtype=torch.float16
            )

        # 🚀 Lade Video-Modell (OpenSora = StableVideoDiffusion-kompatibel)
        self.pipe = StableVideoDiffusionPipeline.from_single_file(
            self.model_path,
            vae=vae,
            torch_dtype=torch.float16,
        ).to("cuda")

        # ✅ Optional: Slicing oder Memory-Optimierung aktivieren
        self.pipe.enable_vae_slicing()
        self.pipe.enable_model_cpu_offload()

        print("✅ OpenSora-Modell erfolgreich geladen!")

    def generate(self, prompt: str, num_frames: int = 24, height: int = 512, width: int = 512):
        if self.pipe is None:
            raise RuntimeError("❌ Modell nicht geladen!")

        print(f"🎬 Prompt: {prompt}")
        result = self.pipe(prompt=prompt, num_frames=num_frames, height=height, width=width)
        return result.videos  # Tensor [B, F, H, W, C]
