FROM ubuntu:22.04

# 🔧 Systempakete installieren
RUN apt update && apt install -y \
    python3 python3-pip bash curl nano git ffmpeg build-essential net-tools \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt install -y nodejs \
    && npm install -g n8n \
    && rm -rf /var/lib/apt/lists/*

# 🌍 Umgebungsvariablen
ENV N8N_PORT=7860
ENV GENERIC_TIMEZONE=Europe/Berlin
ENV N8N_BASIC_AUTH_ACTIVE=false
ENV JUPYTER_TOKEN=""
ENV JUPYTER_ENABLE_LAB=yes

WORKDIR /workspace

# 📦 Projekt reinziehen
COPY . /workspace

# 📦 Python Requirements installieren
RUN pip3 install --no-cache-dir -r requirements.txt || true

# 🧠 Startskript ausführbar machen
RUN chmod +x /workspace/start.sh

# 🚀 Start des Containers
CMD ["/workspace/start.sh"]



