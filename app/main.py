# /workspace/app/main.py
from fastapi import FastAPI
from .wan_api import TI2VRequest, run_wan_ti2v

app = FastAPI(title="WAN 2.2 API", version="1.0")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "WAN_ROOT": "/workspace/Wan2.2",
        "WAN_CKPT_DIR": "/workspace/Wan2.2/Wan2.2-TI2V-5B"
    }

# 🟢 Haupt-Endpunkt für dein Video-Modell
@app.post("/wan/generate")
def wan_generate(request: TI2VRequest):
    """
    Führt eine Text-to-Video-Generierung mit Wan2.2 5B aus.
    Beispielaufruf:
    POST /wan/generate { "prompt": "...", "size": "704*1280", ... }
    """
    return run_wan_ti2v(request)




