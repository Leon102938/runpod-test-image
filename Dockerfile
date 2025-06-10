FROM python:3.10-slim

# Arbeitsverzeichnis setzen
WORKDIR /workspace

# Systempakete installieren
RUN apt update && apt install -y \
    bash \
    procps \
    git \
    curl \
    vim \
    locales \
    ffmpeg \
    build-essential \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt install -y nodejs \
    && npm install -g n8n \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Projektdateien kopieren
COPY . /workspace

# Startskript ausführbar machen
RUN chmod +x /workspace/start.sh

# Ports freigeben
EXPOSE 8888
EXPOSE 5678

# Startskript starten
CMD ["/workspace/start.sh"]


