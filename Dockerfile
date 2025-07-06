FROM python:3.11-slim

# Tools installieren
RUN apt-get update && apt-get install -y \
    git curl unzip sudo tmux nano rclone fuse wget \
 && rm -rf /var/lib/apt/lists/*


# Arbeitsverzeichnis
WORKDIR /workspace

# Alles kopieren
COPY . .
COPY start.sh /workspace/start.sh

# Rechte setzen
RUN chmod +x /workspace/start.sh


# Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Port für FastAPI explizit freigeben
EXPOSE 8000

# Container-Start
CMD ["bash", "start.sh"]






