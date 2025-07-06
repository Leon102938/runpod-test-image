# ⚙️ CUDA 12.1.1 + cuDNN8 + Ubuntu 20.04
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu20.04

# 🧰 Tools & Build-Essentials + Python 3.11 von Deadsnakes
RUN apt-get update && apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    build-essential \
    python3.11 python3.11-venv python3.11-dev python3-pip \
    git curl unzip sudo tmux nano rclone fuse wget && \
    rm -rf /var/lib/apt/lists/*


# 🔁 Python / pip verlinken
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip

# 🧰 Pip upgraden (Fix für html5lib-Fehler)
RUN python3.11 -m pip install --upgrade pip setuptools wheel

# 🧠 Torch manuell installieren
RUN python3.11 -m pip install --no-cache-dir \
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

# ✅ Rechte setzen
RUN chmod +x /workspace/start.sh

# 🧠 Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# 📢 Ports freigeben
EXPOSE 8000
EXPOSE 8888

# 🚀 Start
CMD ["bash", "start.sh"]





