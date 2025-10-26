FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

# --- System & Python 3.11 ----------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common gnupg ca-certificates curl wget unzip tzdata \
    python3.11 python3.11-venv python3.11-dev \
    git git-lfs ffmpeg libsndfile1 libsentencepiece-dev \
    rclone fuse nano tmux aria2 \
 && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# --- pip für Python 3.11 ------------------------------------------------------
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# --- Torch (CUDA 12.1) zuerst, damit flash_attn notfalls import-checks besteht --
RUN python3.11 -m pip install --upgrade pip setuptools wheel packaging && \
    python3.11 -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
      torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# --- flash-attn nur als fertiges Wheel (kein Source-Build, sonst Platz-/Build-Probleme) ---
# Falls für diese Kombi kein Wheel existiert, wird es übersprungen.
RUN python3.11 -m pip install --no-cache-dir --only-binary=:all: \
      "flash-attn>=2.6,<2.9" \
 || echo "⚠️  Kein flash-attn Wheel für diese Umgebung gefunden – überspringe."

# --- Python-Deps der App ------------------------------------------------------
# WICHTIG: requirements.txt darf KEIN torch/vision/audio/flash_attn enthalten.
COPY requirements.txt /tmp/requirements.txt
RUN python3.11 -m pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt && \
    python3.11 -m pip install --no-cache-dir jupyterlab uvicorn fastapi

# --- HuggingFace Caches (optional) -------------------------------------------
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# --- App ---------------------------------------------------------------------
WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/start.sh

EXPOSE 8888 8000
CMD ["/bin/bash","-lc","/workspace/start.sh"]
