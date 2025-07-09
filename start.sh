#!/bin/bash

# Tools-Konfiguration laden
source ./tools.config


# 🌍 BASE_URL automatisch setzen
echo "🌐 Ermittle dynamische RunPod Proxy-URL..."

POD_ID=${RUNPOD_POD_ID}

if [ -z "$POD_ID" ]; then
    echo "❌ FEHLER: RUNPOD_POD_ID nicht gesetzt – .env nicht geschrieben!"
else
    BASE_URL="https://${POD_ID}-8000.proxy.runpod.net"
    export BASE_URL
    echo "BASE_URL=$BASE_URL" > /workspace/.env
    echo "✅ BASE_URL erfolgreich gesetzt: $BASE_URL"
fi

# ============ 🔹 TXT2IMG MODELLE LADEN ============
echo "📦 Starte Modellauswahl aus filelist.txt ..."
mkdir -p /workspace/ai-core/models/txt2img

# CRLF fixen
sed -i 's/\r$//' /workspace/filelist.txt

# Nur herunterladen, wenn < 8 Modelle existieren
MODEL_DIR="/workspace/ai-core/models/txt2img"
MODEL_COUNT=$(ls "$MODEL_DIR"/*.safetensors 2>/dev/null | wc -l)

if [ "$MODEL_COUNT" -lt 8 ]; then
  echo "⏳ Lade txt2img-Modelle..."
  cat /workspace/filelist.txt | xargs -n 1 -P 8 wget --show-progress -P "$MODEL_DIR"
  echo "✅ txt2img-Modelle erfolgreich geladen!"
else
  echo "✅ txt2img-Modelle bereits vorhanden – Überspringe Download."
fi

# ============ 🔹 IMG2VID MODELLE LADEN ============
echo "🎞️ Starte Motion-Modell-Download für img2vid..."
mkdir -p /workspace/ai-core/models/IMG2Vid

# CRLF fixen
sed -i 's/\r$//' /workspace/filelist_img2vid.txt

# Nur herunterladen, wenn Datei noch nicht vorhanden ist
IMG2VID_DIR="/workspace/ai-core/models/IMG2Vid"
MOTION_MODEL_COUNT=$(ls "$IMG2VID_DIR"/*.safetensors 2>/dev/null | wc -l)

if [ "$MOTION_MODEL_COUNT" -lt 1 ]; then
  echo "⏳ Lade img2vid-Motion-Modell..."
  cat /workspace/filelist_img2vid.txt | xargs -n 1 -P 1 wget --show-progress -P "$IMG2VID_DIR"
  echo "✅ Motion-Modell erfolgreich geladen!"
else
  echo "✅ Motion-Modell bereits vorhanden – Überspringe Download."
fi

# ============ 🔧 PYTHONPATH ============
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

# ============ 🔷 FASTAPI (Port 8000) ============
if [ "$FASTAPI" == "on" ]; then
  echo "🚀 Starte zentrale FastAPI (Port 8000)..."
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /workspace/fastapi.log 2>&1 &
fi

# ============ ✅ ABSCHLUSS ============
echo "✅ Dienste wurden gestartet: Modelle geladen, JupyterLab und/oder FastAPI aktiv (je nach config)"
tail -f /dev/null


