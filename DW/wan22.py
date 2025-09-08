# /workspace/Downloads/wan22.py
import os
import sys
import subprocess
import shlex

DST_DIR = "/workspace/Wan2.2/models"

HF_URLS = [
    ("https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/main/Wan2.2_VAE.pth",
     f"{DST_DIR}/Wan2.2_VAE.pth"),
    ("https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors",
     f"{DST_DIR}/diffusion_pytorch_model.safetensors"),
    ("https://huggingface.co/Wan-AI/Wan2.2-TI2V-5B/resolve/main/models_t5_umt5-xxl-enc-bf16.pth",
     f"{DST_DIR}/models_t5_umt5-xxl-enc-bf16.pth"),
]

CF_URLS = [
    ("https://cdn.leoncdn.dev/models/text2Video/Wan2.2/Wan2.2_VAE.pth",
     f"{DST_DIR}/Wan2.2_VAE.pth"),
    ("https://cdn.leoncdn.dev/models/text2Video/Wan2.2/wan2.2_ti2v_5B_fp16.safetensors",
     f"{DST_DIR}/diffusion_pytorch_model.safetensors"),
    ("https://cdn.leoncdn.dev/models/text2Video/Wan2.2/models_t5_umt5-xxl-enc-bf16.pth",
     f"{DST_DIR}/models_t5_umt5-xxl-enc-bf16.pth"),
]

def parse_source() -> str:
    # usage: python wan22.py --source HF|CF
    src = "HF"
    if len(sys.argv) >= 3 and sys.argv[1] == "--source":
        s = sys.argv[2].strip().upper()
        if s in ("HF", "CF", "CLOUDFLARE"):
            src = "CF" if s.startswith("C") else "HF"
    return src

def main() -> int:
    os.makedirs(DST_DIR, exist_ok=True)
    source = parse_source()
    jobs = HF_URLS if source == "HF" else CF_URLS
    print(f"[wan22] source={source}, parallel=3 → {DST_DIR}", flush=True)

    procs = []
    for url, out in jobs:
        cmd = f'wget -c "{url}" -O "{out}" --show-progress --tries=3'
        print("[DL]", out, flush=True)
        procs.append(subprocess.Popen(shlex.split(cmd)))

    rc = 0
    for p in procs:
        rc |= p.wait()
    return rc

if __name__ == "__main__":
    sys.exit(main())
