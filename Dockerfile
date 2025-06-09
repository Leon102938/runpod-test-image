FROM python:3.10-slim

# Arbeitsverzeichnis setzen
WORKDIR /workspace

# Systempakete installieren (für Jupyter & n8n)
RUN apt update && apt install -y \
    git curl ffmpeg bash build-essential gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt install -y nodejs \
    && npm install -g n8n \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt kopieren und installieren (z. B. für jupyterlab)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

# Startskript und sonstige Projektdateien kopieren
COPY . /workspace

# Startskript ausführbar machen
RUN chmod +x /workspace/start.sh

# Ports freigeben
EXPOSE 8888
EXPOSE 5678

# Starten: Jupyter + n8n (aus start.sh)
CMD ["/workspace/start.sh"]

