FROM python:3.10-slim

# Systemabhängigkeiten
RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /workspace

# Python Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Start-Script
COPY start.sh .
RUN chmod +x start.sh

# Startbefehl
CMD ["bash", "start.sh"]
