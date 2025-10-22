# ⚙️ CUDA 12.1.1 + cuDNN8 + Ubuntu 20.04
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

# 🧰 System & PPA (robust für 2025: mit allen Tools, kein KEY.gpg-Direct-Download)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        gnupg2 dirmngr lsb-release \
        curl ca-certificates tzdata; \
    update-ca-certificates; \
    ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime; \
    dpkg-reconfigure -f noninteractive tzdata; \
    add-apt-repository -y ppa:deadsnakes/ppa; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        python3.11 python3.11-venv python3.11-dev python3.11-distutils \
        git git-lfs wget unzip uuid-runtime \
        ffmpeg libsndfile1 libsentencepiece-dev \
        rclone fuse nano tmux aria2; \
    git lfs install; \
    rm -rf /var/lib/apt/lists/*

# 📦 pip für Py3.11 (verlässlich, unabhängig vom System-pip)
RUN set -eux; \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11; \
    ln -sf /usr/bin/python3.11 /usr/bin/python; \
    ln -sf /usr/local/bin/pip /usr/bin/pip; \
    pip install --upgrade pip setuptools wheel packaging

# 🔥 Torch-Stack (CUDA 12.1) – exakt gepinnt
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# (Optional, aber oft stabiler für ältere Wheels)
# RUN pip install --no-cache-dir "numpy<2" "scipy<1.12"

# 📦 Restliche Python-Deps
COPY requirements.txt /tmp/requirements.txt
# Falls deine requirements evtl. flash-attn enthalten (was bauen würde), kannst du es so rausfiltern:
# RUN grep -v -i '^flash[_-]*attn' /tmp/requirements.txt > /tmp/requirements.nofa.txt && mv /tmp/requirements.nofa.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# 🔁 HF-Cache
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# 🔧 Anti-Freeze / Memory-Fragmentation Tweaks (optional, schadet nicht)
ENV PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128" \
    TOKENIZERS_PARALLELISM=false \
    TRANSFORMERS_NO_FAST_TOKENIZER=1 \
    OMP_NUM_THREADS=1

# 📁 Projekt
WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/DW/run.py || true
RUN chmod +x /workspace/start.sh || true

EXPOSE 8000 8888
CMD ["bash", "start.sh"]