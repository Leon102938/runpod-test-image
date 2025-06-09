#!/bin/bash

# JupyterLab starten (HINTERGRUND)
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root &

# n8n starten (im VORDERGRUND)
n8n


