FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu20.04

# 🧰 Tools & Python installieren
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip \
    git curl unzip sudo tmux nano rclone fuse wget \
 && rm -rf /var/lib/apt/lists/*

# 🧠 Python / pip verlinken – wichtig für Kompatibilität
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && ln -sf /usr/bin/pip3 /usr/bin/pip

# 📁 Arbeitsverzeichnis
WORKDIR /workspace

# 🔁 Alles kopieren
COPY . .
COPY start.sh /workspace/start.sh

# ✅ Rechte setzen
RUN chmod +x /workspace/start.sh

# 📦 Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# 📢 Ports freigeben
EXPOSE 8000
EXPOSE 8888

# 🚀 Container-Start
CMD ["bash", "start.sh"]






