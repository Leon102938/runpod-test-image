#!/bin/bash

# Lade Konfig-Datei mit Ein-/Aus-Schaltern
source /workspace/tools.config

# Jupyter starten
if [ "$JUPYTER" == "on" ]; then
    echo "✅ Starte JupyterLab..."
    nohup jupyter lab --ip=0.0.0.0 --port=8888 --no-browser > /workspace/jupyter.log 2>&1 &
else
    echo "⏹️ JupyterLab ist deaktiviert."
fi

# n8n starten
if [ "$N8N" == "on" ]; then
    echo "✅ Starte N8N..."
    nohup n8n > /workspace/n8n.log 2>&1 &
else
    echo "⏹️ N8N ist deaktiviert."
fi

# txt2img FastAPI immer starten (oder auch optional machen)
if [ "$TXT2IMG" == "on" ]; then
    echo "✅ Starte txt2img FastAPI..."
    nohup uvicorn main:app --host 0.0.0.0 --port=8000 > /workspace/txt2img.log 2>&1 &
else
    echo "⏹️ txt2img FastAPI ist deaktiviert."
fi

echo "✅ Alle gewünschten Dienste gestartet. Terminal bereit!"
tail -f /dev/null





