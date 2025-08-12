#!/usr/bin/env python3
# Minimal-Launcher: liest config.txt und startet Worker parallel.

import os, sys, shlex, subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(BASE_DIR, "config.txt")
PY = sys.executable  # gleicher Interpreter wie zum Starten

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
            cfg[k.strip()] = v.strip()
    return cfg

def spawn(script, extra_args=""):
    script_path = os.path.join(BASE_DIR, script)
    if not os.path.exists(script_path):
        print(f"[skip] {script} fehlt, übersprungen")
        return None
    cmd = f'"{PY}" "{script_path}" {extra_args}'.strip()
    print(f"[RUN] {cmd}")
    return subprocess.Popen(shlex.split(cmd), cwd=BASE_DIR)

def main():
    cfg = read_cfg(CFG_PATH)
    procs = []

    # FLASH_ATTENTION = ON|OFF
    if cfg.get("FLASH_ATTENTION", "OFF").strip().upper() == "ON":
        p = spawn("flash_attention.py")
        if p: procs.append(p)

    # THINKSOUND = ON|OFF
    if cfg.get("THINKSOUND", "OFF").strip().upper() == "ON":
        p = spawn("thinksound.py")
        if p: procs.append(p)

    # WAN22 = HF|CF|OFF
    wan = cfg.get("WAN22", "OFF").strip().upper()
    if wan in ("HF", "CF"):
        p = spawn("wan22.py", f"--source {wan}")
        if p: procs.append(p)

    # Auf alle gestarteten Worker warten
    rc = 0
    for p in procs:
        rc |= p.wait()
    return rc

if __name__ == "__main__":
    sys.exit(main())
