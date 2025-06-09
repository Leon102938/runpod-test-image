FROM python:3.10

WORKDIR /workspace

# Systempakete, die das Jupyter-Terminal braucht
RUN apt-get update && apt-get install -y \
    bash \
    procps \
    git \
    curl \
    vim \
    locales \
    && rm -rf /var/lib/apt/lists/*

# JupyterLab installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8888

CMD ["/start.sh"]
