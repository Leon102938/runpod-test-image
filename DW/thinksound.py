#!/usr/bin/env python3
# /workspace/DW/thinksound.py
import os, sys, subprocess, shlex, shutil

BASE_URL = "https://cdn.leoncdn.dev/models/txt2Sound/Thinksound"
DST_DIR  = "/workspace/ThinkSound/ckpts"

BIG = "thinksound.ckpt"  # ~19 GiB: server mag keine vielen Ranges → Single-Stream
FILES = [BIG, "vae.pth", "synchformer_state_dict.pth"]

def log(cmd): print("[RUN]", " ".join(shlex.quote(x) for x in cmd), flush=True)
def run(cmd): log(cmd); return subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
def ensure_dir(p): os.makedirs(p, exist_ok=True)

def ensure_aria2c():
    if shutil.which("aria2c"): return True
    if not shutil.which("apt-get"): return False
    try:
        run(["apt-get","update"])
        run(["apt-get","install","-y","aria2"])
        return bool(shutil.which("aria2c"))
    except Exception:
        return False

def dl_single_curl(url, tmp):
    # HTTP/3 (QUIC) wenn möglich; sonst HTTP/2/1.1 — Single-Stream, Resume
    args = ["curl","-L","--fail","--retry","5","--retry-all-errors",
            "--continue-at","-","--output", tmp, url]
    if shutil.which("curl"):
        # Versuche http3 zuerst (wenn CF + UDP erlaubt)
        rc = run(args[:2] + ["--http3"] + args[2:])
        if rc == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0: return 0
        # Fallback ohne --http3
        return run(args)
    return 1

def dl_single_wget(url, tmp):
    return run(["wget","-c",url,"-O",tmp,"--show-progress","--tries=3",
                "--timeout=60","--read-timeout=60","--dns-timeout=30"])

def dl_single_aria(url, tmp):
    # Ein Stream, große Split-Size → minimale Range-Requests
    if not ensure_aria2c(): return 1
    return run(["aria2c","-x1","-s1","-k16M","--timeout=60","--max-tries=5","--retry-wait=3",
                "--file-allocation=none","--auto-file-renaming=false",
                "-o", os.path.basename(tmp), "-d", "/tmp", url])

def download_big(url, tmp):
    # Reihenfolge: curl --http3 → curl → aria (x1) → wget
    for fn in (dl_single_curl, dl_single_aria, dl_single_wget):
        rc = fn(url, tmp)
        if rc == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
            return 0
    return 1

def download_fast(url, tmp):
    # Für kleinere Files: aria2c adaptiv 8→4→2; Fallback wget
    have = ensure_aria2c()
    if have:
        for c in (8,4,2):
            rc = run(["aria2c",f"-x{c}",f"-s{c}","-k1M","--timeout=30","--max-tries=5","--retry-wait=2",
                      "--file-allocation=none","--auto-file-renaming=false",
                      "-o", os.path.basename(tmp), "-d", "/tmp", url])
            if rc == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
                return 0
    return dl_single_wget(url, tmp)

def get(url, dest, big=False):
    ensure_dir(os.path.dirname(dest))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"[SKIP] {dest} (exists)"); return 0
    tmp = os.path.join("/tmp", os.path.basename(dest))
    try:
        if os.path.exists(tmp): os.remove(tmp)
    except FileNotFoundError:
        pass
    print(f"[DL] {dest}  ←  {url}")
    rc = (download_big if big else download_fast)(url, tmp)
    if rc == 0 and os.path.exists(tmp) and os.path.getsize(tmp) > 0:
        print("[MV]", tmp, "→", dest)
        try: shutil.move(tmp, dest); return 0
        except Exception as e: print("[ERR] move failed:", e); return 1
    print(f"[ERR] download failed: {url}"); return 1

def main():
    ensure_dir(DST_DIR)
    rc = 0
    for fname in FILES:
        url  = f"{BASE_URL}/{fname}"
        dest = os.path.join(DST_DIR, fname)
        rc |= get(url, dest, big=(fname == BIG))
    return 0 if rc == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
