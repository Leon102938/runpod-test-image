FROM python:3.11-slim

# Tools installieren
RUN apt-get update && apt-get install -y \
    git curl unzip sudo tmux nano rclone fuse \
 && rm -rf /var/lib/apt/lists/*


# Arbeitsverzeichnis
WORKDIR /workspace

# Alles kopieren
COPY . .

# Rechte setzen


# Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Container-Start
CMD ["bash", "start.sh"]






