# ⚙️ CUDA 12.1.1 + cuDNN8 + Ubuntu 20.04
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1 TZ=Europe/Berlin

# 🧰 System-Basis (Keyring + deadsnakes-PPA robust einbinden)
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates gnupg lsb-release tzdata && \
    update-ca-certificates && \
    install -d -m 0755 /etc/apt/keyrings && \
    curl -fsSL https://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu/KEY.gpg \
      | gpg --dearmor -o /etc/apt/keyrings/deadsnakes.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/deadsnakes.gpg] \
      http://ppa.launchpadcontent.net/deadsnakes/ppa/ubuntu $(lsb_release -cs) main" \
      > /etc/apt/sources.list.d/deadsnakes.list && \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      python3.11 python3.11-venv python3.11-dev python3.11-distutils \
      git git-lfs wget unzip uuid-runtime \
      ffmpeg libsndfile1 libsentencepiece-dev rclone fuse nano tmux aria2 && \
    git lfs install && \
    rm -rf /var/lib/apt/lists/*

# 📦 pip für Py3.11 (immer zuverlässig)
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip /usr/bin/pip && \
    pip install --upgrade pip setuptools wheel packaging

# 🔥 Torch (cu121) – exakt wie gewünscht
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# 📦 Restliche Python-Deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 🔁 HF-Cache
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# 📁 Projekt
WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/DW/run.py && chmod +x /workspace/start.sh

EXPOSE 8000 8888

CMD ["bash", "start.sh"]