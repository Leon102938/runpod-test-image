#!/usr/bin/env python3
# /workspace/DW/flash_attention.py
import os, sys, subprocess, urllib.parse, shutil

WHEEL_URL = "https://cdn.leoncdn.dev/Flash-Attention/flash_attn-2.5.7-cp311-cp311-linux_x86_64.whl"
DST_DIR   = "/workspace/wheel_flashattn"
DST_FILE  = os.path.join(DST_DIR, os.path.basename(urllib.parse.urlparse(WHEEL_URL).path))

PIP_CMD = None  # wird dynamisch gesetzt

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

def pick_pip():
    """Wählt ein funktionierendes pip aus (pip/pip3 oder python -m pip) und richtet es ggf. ein."""
    global PIP_CMD
    # 1) vorhandenes pip bevorzugen
    for candidate in (["pip"], ["pip3"], [sys.executable, "-m", "pip"]):
        exe = candidate[0]
        if exe == sys.executable or shutil.which(exe):
            if run(candidate + ["--version"]) == 0:
                PIP_CMD = candidate
                return 0

    print("[INFO] pip fehlt – versuche Installation …")
    # 2) apt-get Weg
    if shutil.which("apt-get"):
        if run(["apt-get", "update"]) == 0 and run(["apt-get", "install", "-y", "python3-pip"]) == 0:
            PIP_CMD = [sys.executable, "-m", "pip"]
            return 0

    # 3) get-pip.py Fallback
    gp = "/tmp/get-pip.py"
    if run(["wget", "-q", "https://bootstrap.pypa.io/get-pip.py", "-O", gp]) == 0:
        if run([sys.executable, gp]) == 0:
            PIP_CMD = [sys.executable, "-m", "pip"]
            return 0
    return 1

def pip_install(pkg_path):
    assert PIP_CMD, "pip nicht initialisiert"
    return run(PIP_CMD + ["install", "--no-deps", pkg_path])

def fast_download(url, dst_path):
    """Lädt parallel nach /tmp (NVMe) und verschiebt ins Volume. Fallback: wget."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    tmp = os.path.join("/tmp", os.path.basename(dst_path))
    if shutil.which("aria2c"):
        rc = run(["aria2c", "-x16", "-s16", "-k1M", "-o", os.path.basename(tmp), "-d", "/tmp", url])
        if rc != 0:
            return 1
    else:
        rc = run(["wget", "-c", url, "-O", tmp, "--show-progress", "--tries=3"])
        if rc != 0:
            return 1
    return run(["mv", "-f", tmp, dst_path])

def main():
    if have_flash():
        return 0

    os.makedirs(DST_DIR, exist_ok=True)
    if not (os.path.exists(DST_FILE) and os.path.getsize(DST_FILE) > 0):
        if fast_download(WHEEL_URL, DST_FILE) != 0 or not os.path.exists(DST_FILE):
            print("[ERR] Download fehlgeschlagen.")
            return 1

    if pick_pip() != 0:
        print("[ERR] pip konnte nicht eingerichtet werden.")
        return 1

    if pip_install(DST_FILE) != 0:
        print("[ERR] Installation fehlgeschlagen. Prüfe Python-Version vs. Wheel-Tag (cp311).")
        return 1

    if have_flash():
        print("[OK] flash_attn installiert.")
        return 0

    print("[ERR] flash_attn nach Installation nicht importierbar.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
