FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
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
# get-pip erzeugt bereits /usr/local/bin/pip und pip3 → keinen zweiten Symlink auf pip3 anlegen!
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
 && /usr/bin/python3.11 /tmp/get-pip.py \
 && ln -sf /usr/bin/python3.11 /usr/local/bin/python \
 && rm -f /tmp/get-pip.py

# Optional: Wenn du trotzdem explizit sicherstellen willst:
# RUN [ -e /usr/local/bin/pip3 ] || ln -s /usr/local/bin/pip /usr/local/bin/pip3

# --- PyTorch 2.4.0 für CUDA 12.1 (cu121 Index) --------------------------------
RUN python -m pip install --no-cache-dir \
      --index-url https://download.pytorch.org/whl/cu121 \


# --- HF-Caches ----------------------------------------------------------------
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub


WORKDIR /workspace


EXPOSE 8000 8888
CMD ["bash", "start.sh"]