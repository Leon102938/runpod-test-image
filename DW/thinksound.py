#!/usr/bin/env python3
# /workspace/DW/thinksound.py
import os, subprocess, shlex, sys

DST_DIR = "/workspace/ThinkSound/ckpts"

JOBS = [
    # 1) ThinkSound Haupt-Checkpoint
    ("https://cdn.leoncdn.dev/models/txt2Sound/Thinksound/thinksound.ckpt",
     f"{DST_DIR}/thinksound.ckpt"),
    # 2) VAE
    ("https://cdn.leoncdn.dev/models/txt2Sound/Thinksound/thinksound_vae.pth",
     f"{DST_DIR}/thinksound_vae.pth"),
    # 3) SyncFormer State Dict
    ("https://cdn.leoncdn.dev/models/txt2Sound/Thinksound/synchformer_state_dict.pth",
     f"{DST_DIR}/synchformer_state_dict.pth"),
]

def main() -> int:
    os.makedirs(DST_DIR, exist_ok=True)

    procs = []
    for url, out in JOBS:
        cmd = f'wget -c "{url}" -O "{out}" --show-progress --tries=3 --timeout=30 --read-timeout=30 --dns-timeout=10'
        print("[DL]", out, flush=True)
        procs.append(subprocess.Popen(shlex.split(cmd)))

    rc = 0
    for p in procs:
        rc |= p.wait()
    return rc

if __name__ == "__main__":
    sys.exit(main())
