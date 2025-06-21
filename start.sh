#!/bin/bash

# Tools-Konfiguration laden
source ./tools.config

# Pythonpath setzen (damit FastAPI die Module findet)
export PYTHONPATH="$PYTHONPATH:/workspace/app"

# Mount-Volume starten
bash ./mount_server_volume.sh

# ============ 🔷 JUPYTERLAB (Port 8888) ============
if [ "$JUPYTER" == "on" ]; then
  echo "🧠 Starte JupyterLab (Port 8888)..."
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
fi

# ============ 🧩 FASTAPI (Port 7860) ============
if [ "$FASTAPI" == "on" ]; then
  echo "🚀 Starte zentrale FastAPI (Port 7860)..."
  nohup uvicorn app.main:app --host 0.0.0.0 --port 7860 > /workspace/fastapi.log 2>&1 &
fi

# ============ ✅ ABSCHLUSS ============
echo "✅ Dienste wurden gestartet: JupyterLab und/oder FastAPI (je nach config)"
tail -f /dev/null
