FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# System + Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common gnupg ca-certificates curl wget unzip tzdata \
    python3.11 python3.11-venv python3.11-dev git git-lfs ffmpeg \
    libsndfile1 libsentencepiece-dev rclone fuse nano tmux aria2 \
 && ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# pip für 3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# *** Torch separat (und NICHT in requirements.txt doppeln!) ***
RUN python3.11 -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# Restliche Deps
COPY requirements.txt /tmp/requirements.txt
# (requirements.txt OHNE torch/vision/audio)
RUN python3.11 -m pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt \
 && python3.11 -m pip install --no-cache-dir jupyterlab uvicorn fastapi

ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/start.sh

EXPOSE 8888 8000
CMD ["/bin/bash","-lc","/workspace/start.sh"]