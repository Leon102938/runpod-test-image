# /workspace/Downloads/flash_attention.py
import os
import subprocess
import sys

WHEEL_URL = "https://cdn.leoncdn.dev/Flash-Attention/flash_attn-2.5.7-cp311-cp311-linux_x86_64.whl"
DST_DIR   = "/workspace/wheel_flashattn"
DST_FILE  = os.path.join(DST_DIR, os.path.basename(WHEEL_URL))

def sh(cmd: list[str]) -> int:
    print("[RUN]", " ".join(cmd), flush=True)
    return subprocess.call(cmd)

def main() -> int:
    os.makedirs(DST_DIR, exist_ok=True)

    # 1) Download (resumefähig, mit Fortschritt)
    rc = sh(["wget", "-c", WHEEL_URL, "-O", DST_FILE, "--show-progress", "--tries=3"])
    if rc != 0 or not os.path.exists(DST_FILE):
        print(f"[ERR] Download fehlgeschlagen oder Datei fehlt: {DST_FILE}", flush=True)
        return 1

    # 2) Install (ohne Abhängigkeiten zu überschreiben)
    rc = sh(["pip", "install", "--no-deps", DST_FILE])
    if rc != 0:
        print("[ERR] pip install fehlgeschlagen.", flush=True)
    return rc

if __name__ == "__main__":
    sys.exit(main())
