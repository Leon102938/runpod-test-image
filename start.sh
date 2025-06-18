#!/bin/bash

export SHELL=/bin/bash
echo "🚀 Starte Setup-Prozess..."

# ─────────────── JUPYTER ───────────────
echo "✅ Starte JupyterLab (Port 8888)..."
nohup jupyter lab \
    --ip=0.0.0.0 \
    --port=8888 \
    --no-browser \
    --allow-root \
    --NotebookApp.token='' \
    --NotebookApp.password='' \
    --NotebookApp.disable_check_xsrf=True \
    --NotebookApp.notebook_dir='/workspace' \
    --ServerApp.allow_origin='*' \
    > /workspace/jupyter.log 2>&1 &

# ─────────────── FASTAPI ───────────────
echo "🎨 Starte zentrale FastAPI (Port 8000)..."
nohup uvicorn app.main:app --host 0.0.0.0 --port=8000 > /workspace/fastapi.log 2>&1 &

# ─────────────── ABSCHLUSS ───────────────
echo "✅ Dienste wurden gestartet: JupyterLab + FastAPI"
tail -f /dev/null





