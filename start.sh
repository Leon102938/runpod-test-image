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


# ============ 🔷 Download ============
if [ "$Init" = "on" ]; then
  echo "🚀 Starte WAN-Init"
  if [ -x /workspace/init.sh ]; then
    nohup bash /workspace/init.sh >/dev/null 2>&1 & disown
  else
    echo "⚠️  /workspace/init.sh nicht gefunden oder nicht ausführbar."
  fi
else
  echo "⏭️  Init=off – überspringe WAN-Download."
fi

# ============ ✅ ABSCHLUSS ============
echo "✅ Dienste wurden gestartet: Modelle geladen, JupyterLab und/oder FastAPI aktiv (je nach config)"
tail -f /dev/null


