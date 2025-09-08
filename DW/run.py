#!/usr/bin/env python3
# Minimal-Launcher: liest config.txt und startet Worker parallel.

import os, sys, shlex, subprocess, shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, "config.txt")

# Bevorzugt 3.11, damit cp311-Wheels (flash_attn) sicher importierbar sind.
PY = os.environ.get("PY") or shutil.which("python3.11") or sys.executable

def read_cfg(path):
    cfg = {}
    if not os.path.exists(path):
        return cfg
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip().upper()] = v.strip()
    return cfg

def spawn(script, extra_args=""):
    script_path = os.path.join(BASE_DIR, script)
    if not os.path.exists(script_path):
        print(f"[skip] {script} fehlt, übersprungen")
        return None
    cmd = [PY, script_path] + (shlex.split(extra_args) if extra_args else [])
    print("[RUN]", " ".join(shlex.quote(x) for x in cmd))
    return subprocess.Popen(cmd, cwd=BASE_DIR)

def main():
    cfg = read_cfg(CFG_PATH)
    procs = []

    # FLASH_ATTENTION = ON|OFF ; FLASH_ATTENTION_ARGS = ...
    if cfg.get("FLASH_ATTENTION", "OFF") == "ON":
        p = spawn("flash_attention.py", cfg.get("FLASH_ATTENTION_ARGS", ""))
        if p: procs.append(p)

    # THINKSOUND = ON|OFF ; THINKSOUND_ARGS = ...
    if cfg.get("THINKSOUND", "OFF") == "ON":
        p = spawn("thinksound.py", cfg.get("THINKSOUND_ARGS", ""))
        if p: procs.append(p)

    # WAN22 = HF|CF|OFF ; WAN22_ARGS = ...
    wan = cfg.get("WAN22", "OFF")
    if wan in ("HF", "CF"):
        extra = f"--source {wan}"
        if cfg.get("WAN22_ARGS"):
            extra += f" {cfg['WAN22_ARGS']}"
        p = spawn("wan22.py", extra)
        if p: procs.append(p)

    rc = 0
    for p in procs:
        rc |= p.wait()
    return rc

if __name__ == "__main__":
    sys.exit(main())
