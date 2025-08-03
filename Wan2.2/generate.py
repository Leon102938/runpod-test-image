# ✅ FINAL generate.py für WAN 2.2 TI2V, mit vollständigem Logging, Debug und klarer Struktur
# 🔥 Einfach ersetzen, starten, fertig.

import argparse
import logging
import os
import random
import sys
from datetime import datetime
from PIL import Image
import torch
import torch.distributed as dist
import warnings

warnings.filterwarnings("ignore")

import wan
from wan.configs.wan_ti2v_5B import ti2v_5B
from wan.distributed.util import init_distributed_group
from wan.utils.prompt_extend import DashScopePromptExpander, QwenPromptExpander
from wan.utils.utils import save_video, str2bool

WAN_CONFIGS = {"ti2v-5B": ti2v_5B}
SUPPORTED_SIZES = {"ti2v-5B": ["1280*704", "512*320", "1024*640"]}
SIZE_CONFIGS = {s: tuple(map(int, s.split("*"))) for s in SUPPORTED_SIZES["ti2v-5B"]}
MAX_AREA_CONFIGS = {k: w * h for k, (w, h) in SIZE_CONFIGS.items()}

def _parse_args():
    parser = argparse.ArgumentParser(description="WAN 2.2 TI2V Video Generator")
    parser.add_argument("--task", type=str, default="ti2v-5B")
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--ckpt_dir", type=str, required=True)
    parser.add_argument("--image", type=str, default=None)
    parser.add_argument("--size", type=str, default="1280*704", choices=SUPPORTED_SIZES["ti2v-5B"])
    parser.add_argument("--frame_num", type=int, default=16)
    parser.add_argument("--sample_steps", type=int, default=25)
    parser.add_argument("--sample_shift", type=float, default=8)
    parser.add_argument("--sample_guide_scale", type=float, default=6.0)
    parser.add_argument("--base_seed", type=int, default=-1)
    parser.add_argument("--offload_model", type=str2bool, default=True)
    parser.add_argument("--t5_fsdp", action="store_true")
    parser.add_argument("--dit_fsdp", action="store_true")
    parser.add_argument("--t5_cpu", action="store_true")
    parser.add_argument("--ulysses_size", type=int, default=1)
    parser.add_argument("--convert_model_dtype", action="store_true")
    parser.add_argument("--save_file", type=str, default=None)
    return parser.parse_args()

def _init_logging():
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

def generate(args):
    _init_logging()
    rank = 0
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    logging.info("🧠 Initializing pipeline...")
    logging.info(f"Task: {args.task}, Prompt: {args.prompt}")
    logging.info(f"Checkpoint dir: {args.ckpt_dir}")

    if args.base_seed < 0:
        args.base_seed = random.randint(0, 9999999999)
    logging.info(f"🔁 Using Seed: {args.base_seed}")

    cfg = WAN_CONFIGS[args.task]
    size = SIZE_CONFIGS[args.size]
    max_area = MAX_AREA_CONFIGS[args.size]

    image = None
    if args.image:
        if not os.path.exists(args.image):
            logging.error(f"❌ Image not found: {args.image}")
            sys.exit(1)
        image = Image.open(args.image).convert("RGB")
        logging.info(f"🖼️ Loaded input image: {args.image}")

    logging.info("🚀 Loading WAN TI2V pipeline...")
    pipeline = wan.WanTI2V(
        config=cfg,
        checkpoint_dir=args.ckpt_dir,
        device_id=0,
        rank=rank,
        t5_fsdp=args.t5_fsdp,
        dit_fsdp=args.dit_fsdp,
        use_sp=(args.ulysses_size > 1),
        t5_cpu=args.t5_cpu,
        convert_model_dtype=args.convert_model_dtype,
    )

    logging.info("🎞️ Starting generation...")
    video = pipeline.generate(
        input_prompt=args.prompt,
        img=image,
        size=size,
        max_area=max_area,
        frame_num=args.frame_num,
        shift=args.sample_shift,
        sample_solver="unipc",
        sampling_steps=args.sample_steps,
        guide_scale=args.sample_guide_scale,
        seed=args.base_seed,
        offload_model=args.offload_model,
    )

    if args.save_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_str = args.prompt.replace(" ", "_")[:50]
        args.save_file = f"wan_ti2v_{prompt_str}_{timestamp}.mp4"

    print(f"[DEBUG] video shape: {video.shape}, dtype: {video.dtype}, min: {video.min().item():.4f}, max: {video.max().item():.4f}")

    
    logging.info(f"💾 Saving video to {args.save_file}")
    save_video(video[None], args.save_file, fps=cfg.sample_fps, nrow=1, normalize=True, value_range=(-1, 1))

    torch.cuda.synchronize()
    logging.info("✅ Generation finished.")

if __name__ == "__main__":
    args = _parse_args()
    generate(args)
