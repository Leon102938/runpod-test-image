FROM nvidia/cuda:12.2.0-base-ubuntu22.04

WORKDIR /workspace

RUN apt update && apt install -y \
    python3.10 \
    python3-pip \
    git \
    && apt clean

COPY requirements.txt .
RUN python3.10 -m pip install -r requirements.txt

COPY . .

# ENTRYPOINT explizit setzen für Vast
ENTRYPOINT ["/bin/bash"]

# Startscript wird dann als Argument übergeben
CMD ["start.sh"]






