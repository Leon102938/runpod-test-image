# CUDA 12.1.1 + cuDNN 8 (Ubuntu 22.04)  ✅ existierender Tag
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# --- System + Python 3.11 ----------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
      software-properties-common gnupg ca-certificates curl wget unzip tzdata \
      build-essential git git-lfs ffmpeg libsndfile1 libsentencepiece-dev \
      rclone fuse nano tmux aria2 \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update && apt-get install -y --no-install-recommends \
      python3.11 python3.11-venv python3.11-dev \
 && ln -sf /usr/share/zoneinfo/$TZ /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# --- pip für Python 3.11 ------------------------------------------------------
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
 && /usr/bin/python3.11 /tmp/get-pip.py \
 && ln -s /usr/bin/python3.11 /usr/local/bin/python \
 && ln -s /usr/local/bin/pip /usr/local/bin/pip3 \
 && rm -f /tmp/get-pip.py

# --- PyTorch 2.4.0 für CUDA 12.1 (cu121 Index) --------------------------------
RUN /usr/local/bin/pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cu121 \
      torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# --- Python-Deps aus requirements.txt -----------------------------------------
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# --- HF-Caches ----------------------------------------------------------------
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# --- Projekt ------------------------------------------------------------------
WORKDIR /workspace
COPY . .
# Falls die Dateien nicht existieren, nicht hart fehlschlagen:
RUN chmod +x /workspace/DW/run.py || true \
 && chmod +x /workspace/start.sh || true

EXPOSE 8000 8888
CMD ["bash", "start.sh"]