FROM python:3.11-slim

# Tools installieren (fuse ggf. optional, wenn wirklich gebraucht)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl unzip sudo tmux nano fuse \
 && rm -rf /var/lib/apt/lists/*

# rclone installieren
RUN curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip && \
    unzip rclone-current-linux-amd64.zip && \
    cp rclone-*-linux-amd64/rclone /usr/bin/ && \
    chmod 755 /usr/bin/rclone && \
    rm -rf rclone-*-linux-amd64 rclone-current-linux-amd64.zip

WORKDIR /workspace

# Kopiere nur notwendige Dateien (COPY . . ist riskant, besser spezifisch)
COPY start.sh /root/start.sh
COPY config/rclone.conf /root/.config/rclone/rclone.conf
COPY requirements.txt /workspace/

RUN chmod +x /root/start.sh

# Python-Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Standard-Startkommando
CMD ["/root/start.sh"]






