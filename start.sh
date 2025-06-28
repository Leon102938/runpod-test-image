#!/bin/bash

# Tools-Konfiguration laden
source ./tools.config

# ============ 🔹 MODELLE LADEN ============
echo "📦 Starte Modellauswahl aus filelist.txt ..."
mkdir -p /workspace/ai-core/models/txt2img

# CRLF (Windows-Zeilenumbrüche) fixen
sed -i 's/\r$//' /workspace/filelist.txt

# Modelle parallel laden
echo "⏳ Lade Modelle (parallel, max 8 gleichzeitig)..."
cat /workspace/filelist.txt | xargs -n 1 -P 8 wget --show-progress -P /workspace/ai-core/models/txt2img

echo "✅ Modelle erfolgreich geladen!"

# Pythonpath setzen (damit FastAPI die Module findet)
export PYTHONPATH="$PYTHONPATH:/workspace/app"


# ============ 🔷 JUPYTERLAB THEME ============
mkdir -p /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension
echo '{ "theme": "JupyterLab Dark" }' > /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/themes.jupyterlab-settings

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

# ============ 🔷 FASTAPI (Port 7860) ============
if [ "$FASTAPI" == "on" ]; then
  echo "🚀 Starte zentrale FastAPI (Port 7860)..."
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /workspace/fastapi.log 2>&1 &
fi

# ============ ✅ ABSCHLUSS ============
echo "✅ Dienste wurden gestartet: Modelle geladen, JupyterLab und/oder FastAPI aktiv (je nach config)"
tail -f /dev/null