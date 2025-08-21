# ⚙️ CUDA 12.1.1 + cuDNN8 + Ubuntu 20.04
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# 🧰 System + Py3.11 (+ nötige Audio-Libs)
# 1) APT (inkl. libsndfile1)
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3.11 python3.11-venv python3.11-dev \
    git git-lfs curl wget unzip tzdata ca-certificates uuid-runtime \
    ffmpeg libsndfile1 libsentencepiece-dev rclone fuse nano tmux aria2 && \
    update-ca-certificates && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && git lfs install && \
    rm -rf /var/lib/apt/lists/*

# 2) pip für Py3.11
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip /usr/bin/pip && \
    pip install --upgrade pip setuptools wheel packaging

# 3) Torch (cu121) separat (bleibt gecached)
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0




# 📦 Restliche Python-Deps
# 4) Rest über requirements.txt (einmal!)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt



# 🔁 HF-Cache (einmalig)
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# 📁 Projekt
WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/start.sh

EXPOSE 8000 8888
CMD ["bash", "start.sh"]