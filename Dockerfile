FROM nvidia/cuda:12.1.1-cudnn9-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

# APT + Python 3.11 (robust, inkl. GnuPG für PPA)
RUN apt-get update && apt-get install -y --no-install-recommends \
      software-properties-common gnupg ca-certificates curl wget unzip tzdata \
      build-essential git git-lfs ffmpeg libsndfile1 libsentencepiece-dev rclone fuse nano tmux aria2 \
 && add-apt-repository -y ppa:deadsnakes/ppa \
 && apt-get update && apt-get install -y --no-install-recommends \
      python3.11 python3.11-venv python3.11-dev \
 && ln -s /usr/bin/python3.11 /usr/local/bin/python \
 && curl -sS https://bootstrap.pypa.io/get-pip.py | /usr/bin/python3.11 \
 && /usr/local/bin/python -m pip install --upgrade pip setuptools wheel packaging \
 && ln -s /usr/local/bin/pip /usr/local/bin/pip3 \
 && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && rm -rf /var/lib/apt/lists/*

# Torch cu121
RUN /usr/local/bin/python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu121 \
      torch==2.4.0 torchvision==0.19.0 torchaudio==2.4.0

# Deps
COPY requirements.txt /tmp/requirements.txt
RUN /usr/local/bin/python -m pip install --no-cache-dir -r /tmp/requirements.txt

ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

WORKDIR /workspace
COPY . .
RUN chmod +x /workspace/DW/run.py && chmod +x /workspace/start.sh

EXPOSE 8000 8888
CMD ["bash","start.sh"]