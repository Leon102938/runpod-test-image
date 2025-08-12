#!/usr/bin/env python3
# /workspace/DW/flash_attention.py
import os, sys, subprocess, urllib.parse, shutil

WHEEL_URL = "https://cdn.leoncdn.dev/Flash-Attention/flash_attn-2.5.7-cp311-cp311-linux_x86_64.whl"
DST_DIR   = "/workspace/wheel_flashattn"
DST_FILE  = os.path.join(DST_DIR, os.path.basename(urllib.parse.urlparse(WHEEL_URL).path))

def run(cmd):
    print("[RUN]", " ".join(cmd), flush=True)
    return subprocess.call(cmd)

def have_flash():
    try:
        import flash_attn  # noqa
        print("[OK] flash_attn bereits installiert – skip.")
        return True
    except Exception:
        return False

def ensure_pip():
    if run([sys.executable, "-m", "pip", "--version"]) == 0:
        return 0
    print("[INFO] pip fehlt – versuche Installation …")
    # apt-get Weg
    if shutil.which("apt-get"):
        if run(["apt-get","update"]) == 0 and run(["apt-get","install","-y","python3-pip"]) == 0:
            return 0
    # Fallback get-pip.py
    gp = "/tmp/get-pip.py"
    if run(["wget","-q","https://bootstrap.pypa.io/get-pip.py","-O",gp]) == 0:
        return run([sys.executable, gp])
    return 1

def main():
    if have_flash():
        return 0

    os.makedirs(DST_DIR, exist_ok=True)
    # Wheel nur laden, wenn es nicht schon da ist
    if not (os.path.exists(DST_FILE) and os.path.getsize(DST_FILE) > 0):
        rc = run(["wget","-c",WHEEL_URL,"-O",DST_FILE,"--show-progress","--tries=3"])
        if rc != 0 or not os.path.exists(DST_FILE):
            print("[ERR] Download fehlgeschlagen.")
            return 1

    # pip sicherstellen
    if ensure_pip() != 0:
        print("[ERR] pip konnte nicht eingerichtet werden.")
        return 1

    # *** immer installieren – genau wie dein Befehl, aber robust via python -m pip ***
    rc = run([sys.executable, "-m", "pip", "install", "--no-deps", DST_FILE])
    if rc != 0:
        print("[ERR] Installation fehlgeschlagen. Prüfe Python-Version vs. Wheel-Tag (cp311).")
        return rc

    # Verify
    if have_flash():
        print("[OK] flash_attn installiert.")
        return 0
    print("[ERR] flash_attn nach Installation nicht importierbar.")
    return 1

if __name__ == "__main__":
    sys.exit(main())

