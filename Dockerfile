# ⚙️ CUDA 12.1.1 + cuDNN8 + Ubuntu 20.04
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu20.04

# 🚫 Verhindert interaktive Prompts wie bei tzdata
ENV DEBIAN_FRONTEND=noninteractive

# 🧰 Tools & Python 3.11
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    build-essential \
    python3.11 python3.11-venv python3.11-dev \
    tzdata \
    git curl unzip sudo nano tmux aria2 wget rclone fuse \
    libsentencepiece-dev ffmpeg && \
    ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 🔁 Huggingface Cache (optional)
ENV HF_HOME=/workspace/.cache/huggingface
ENV TRANSFORMERS_CACHE=$HF_HOME/transformers
ENV HF_HUB_CACHE=$HF_HOME/hub

# 🐍 Python + Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip /usr/bin/pip

RUN pip install --upgrade pip setuptools wheel packaging

# 🧠 PyTorch CUDA 12.1
RUN pip install --no-cache-dir \
    torch==2.4.0 \
    torchvision==0.19.0 \
    torchaudio==2.4.0 \
    networkx==3.2.1 \
    --index-url https://download.pytorch.org/whl/cu121

# 📁 Arbeitsverzeichnis setzen
WORKDIR /workspace

# 🔁 Dateien ins Image kopieren
COPY . .
COPY start.sh /workspace/start.sh

# ✅ Script ausführbar machen
RUN chmod +x /workspace/start.sh

# 📦 Python-Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt


# ⚙️ HF-Cache optimieren (optional, aber empfohlen)
ENV HF_HOME=/workspace/.cache/huggingface
ENV TRANSFORMERS_CACHE=$HF_HOME/transformers
ENV HF_HUB_CACHE=$HF_HOME/hub

# 📢 Ports
EXPOSE 8000
EXPOSE 8888

# 🚀 Startkommando
CMD ["bash", "start.sh"]