#!/bin/bash

export SHELL=/bin/bash
source /workspace/tools.config

echo "🚀 Starte Setup-Prozess..."

# ─────────────── JUPYTER ───────────────
if [ "$JUPYTER" == "on" ]; then
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
else
    echo "⏹️ JupyterLab ist deaktiviert."
fi

# ─────────────── N8N ───────────────
if [ "$N8N" == "on" ]; then
    echo "✅ Starte N8N (Port 7860)..."
    nohup n8n --port 7860 > /workspace/n8n.log 2>&1 &
else
    echo "⏹️ N8N ist deaktiviert."
fi

# ─────────────── TEXT-IMG ───────────────
if [ "$TXT2IMG" == "on" ]; then
    echo "🎨 Starte TEXT2IMG (Port 8000)..."
    nohup uvicorn app.text2img:app --host 0.0.0.0 --port=8000 > /workspace/txt2img.log 2>&1 &
else
    echo "⏹️ TEXT2IMG ist deaktiviert."
fi

# ─────────────── IMG-VID ───────────────
if [ "$IMG2VID" == "on" ]; then
    echo "🎞️ Starte IMG2VID (Port 2000)..."
    nohup uvicorn app.img2vid:app --host 0.0.0.0 --port=2000 > /workspace/img2vid.log 2>&1 &
else
    echo "⏹️ IMG2VID ist deaktiviert."
fi

# ─────────────── TEXT-VID ───────────────
if [ "$TEXT2VID" == "on" ]; then
    echo "🎬 Starte TEXT2VID (Port 3000)..."
    nohup uvicorn app.text2vid:app --host 0.0.0.0 --port=3000 > /workspace/text2vid.log 2>&1 &
else
    echo "⏹️ TEXT2VID ist deaktiviert."
fi

# ─────────────── TEXT-MUSIK ───────────────
if [ "$TEXT2MUSIK" == "on" ]; then
    echo "🎵 Starte TEXT2MUSIK (Port 4000)..."
    nohup uvicorn app.text2musik:app --host 0.0.0.0 --port=4000 > /workspace/text2musik.log 2>&1 &
else
    echo "⏹️ TEXT2MUSIK ist deaktiviert."
fi

# ─────────────── TEXT-VOICE ───────────────
if [ "$TEXT2VOICE" == "on" ]; then
    echo "🗣️ Starte TEXT2VOICE (Port 5000)..."
    nohup uvicorn app.text2voice:app --host 0.0.0.0 --port=5000 > /workspace/text2voice.log 2>&1 &
else
    echo "⏹️ TEXT2VOICE ist deaktiviert."
fi

# ─────────────── TEXT-FSX ───────────────
if [ "$TEXT2FSX" == "on" ]; then
    echo "🌐 Starte TEXT2FSX (Port 6000)..."
    nohup uvicorn app.text2fsx:app --host 0.0.0.0 --port=6000 > /workspace/text2fsx.log 2>&1 &
else
    echo "⏹️ TEXT2FSX ist deaktiviert."
fi

# ─────────────── Abschluss ───────────────
echo "✅ Alle gewünschten Dienste wurden gestartet!"
tail -f /dev/null





