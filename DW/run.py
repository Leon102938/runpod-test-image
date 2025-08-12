# /workspace/Downloads/run.py
import os
import shlex
import subprocess
from typing import Dict

CFG_PATH = "/workspace/Downloads/config.txt"
BASE_DIR = "/workspace/Downloads"

def read_cfg(path: str) -> Dict[str, str]:
    """Liest key=value, ignoriert Leerzeilen, ganze & inline-Kommentare (# ...)."""
    cfg: Dict[str, str] = {}
    if not os.path.exists(path):
        return cfg
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            # inline-Kommentar abschneiden
            line = raw.split("#", 1)[0].strip()
            if not line or "=" not in line:
                continue
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg

def spawn(cmd: str) -> subprocess.Popen:
    print(f"[RUN] {cmd}", flush=True)
    return subprocess.Popen(shlex.split(cmd), cwd=BASE_DIR)

def main() -> int:
    cfg = read_cfg(CFG_PATH)

    procs = []

    # FLASH_ATTENTION = ON|OFF
    if cfg.get("FLASH_ATTENTION", "OFF").strip().upper() == "ON":
        procs.append(spawn("python flash_attention.py"))

    # THINKSOUND = ON|OFF
    if cfg.get("THINKSOUND", "OFF").strip().upper() == "ON":
        procs.append(spawn("python thinksound.py"))

    # WAN22 = HF|CF|OFF
    wan_mode = cfg.get("WAN22", "OFF").strip().upper()
    if wan_mode in ("HF", "CF"):
        procs.append(spawn(f"python wan22.py --source {wan_mode}"))

    # Auf alle parallel gestarteten Tasks warten; kombinierten RC zurückgeben
    rc = 0
    for p in procs:
        rc |= p.wait()
    return rc

if __name__ == "__main__":
    raise SystemExit(main())
