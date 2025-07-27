FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu20.04

# 🧰 Tools & Python 3.11
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    build-essential \
    python3.11 python3.11-venv python3.11-dev \
    git curl unzip sudo nano tmux aria2 wget rclone fuse \
    libsentencepiece-dev ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 🐍 Python + Pip
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11 && \
    ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/local/bin/pip /usr/bin/pip

RUN pip install --upgrade pip setuptools wheel packaging

# 🧠 PyTorch CUDA 12.1
RUN pip install --no-cache-dir \
    torch==2.2.2 \
    torchvision==0.17.2 \
    torchaudio==2.2.2 \
    networkx==3.2.1 \
    --index-url https://download.pytorch.org/whl/cu121

# 📁 Arbeitsverzeichnis
WORKDIR /workspace

# 🔁 Dateien kopieren
COPY . .
COPY start.sh /workspace/start.sh
RUN chmod +x /workspace/start.sh

# 🧠 Abhängigkeiten
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