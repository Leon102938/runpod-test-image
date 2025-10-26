FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04


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



# Nach apt-Installation von python3.11 …
RUN curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py \
 && /usr/bin/python3.11 /tmp/get-pip.py \
 && rm -f /tmp/get-pip.py

# Optional, wenn du "pip" Kommandos (ohne python -m) benutzen willst:
RUN ln -sf /usr/local/bin/pip /usr/bin/pip \
 && ln -sf /usr/bin/python3.11 /usr/bin/python



# 📦 Restliche Python-Deps
# 4) Rest über requirements.txt (einmal!)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt



# 🔁 HF-Cache (einmalig)
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub




# 🔁 Dateien kopieren
WORKDIR /workspace
COPY . .

# ✅ Rechte setzen
RUN chmod +x /workspace/start.sh




EXPOSE 8000 8888
CMD ["bash", "start.sh"]