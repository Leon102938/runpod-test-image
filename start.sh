#!/bin/bash

# Tools-Konfiguration laden
source ./tools.config

# Mount-Volume starten
bash ./mount_server_volume.sh

# Jupyter starten (wenn aktiviert)
if [ "$JUPYTER" == "on" ]; then
  echo "[START] Starte Jupyter..."
  jupyter lab --notebook-dir=/workspace --allow-root --ip=0.0.0.0 --port=8888 --no-browser &
fi

# FastAPI starten (wenn aktiviert)
if [ "$FASTAPI" == "on" ]; then
  echo "[START] Starte FastAPI..."
  uvicorn app.main:app --host 0.0.0.0 --port 7860 &
fi

# Container am Leben halten
tail -f /dev/null
