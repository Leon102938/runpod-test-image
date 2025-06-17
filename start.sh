#!/bin/bash


# Jupyter starten
    echo "✅ Starte JupyterLab..."
    nohup jupyter lab --ip=0.0.0.0 --port=8888 --no-browser > /workspace/jupyter.log 2>&1 &


# n8n starten
    echo "✅ Starte N8N..."
    nohup n8n > /workspace/n8n.log 2>&1 &



# txt2img FastAPI immer starten (oder auch optional machen)
    echo "✅ Starte txt2img FastAPI..."
    nohup uvicorn main:app --host 0.0.0.0 --port=8000 > /workspace/txt2img.log 2>&1 &


echo "✅ Alle gewünschten Dienste gestartet. Terminal bereit!"
tail -f /dev/null





