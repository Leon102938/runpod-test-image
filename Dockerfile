# ✅ Offizielle PyTorch-Basis: Torch 2.4.1 + CUDA 12.1 + cuDNN 9
FROM pytorch/pytorch:2.4.1-cuda12.1-cudnn9-devel

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin \
    # Runtime-Flags gegen „silent freeze“ & für stabilen Speicher
    TOKENIZERS_PARALLELISM=false \
    TRANSFORMERS_NO_FAST_TOKENIZER=1 \
    HF_HOME=/workspace/.cache/huggingface \
    HF_HUB_ENABLE_HF_TRANSFER=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:256 \
    CUDA_DEVICE_MAX_CONNECTIONS=1

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    git git-lfs build-essential pkg-config \
    ffmpeg libsndfile1 libgl1 libsm6 libxext6 \
    curl wget unzip ca-certificates nano tmux aria2 rclone fuse tzdata \
 && git lfs install && rm -rf /var/lib/apt/lists/*

# ---- pip basics ----
RUN python -m pip install --upgrade pip setuptools wheel packaging ninja

# ---- Wan2.2 Code holen (oder du mountest später) ----
WORKDIR /opt
RUN git clone --depth=1 https://github.com/Wan-Video/Wan2.2.git
WORKDIR /opt/Wan2.2

# Wichtig laut Repo: Torch >= 2.4.0 ist schon im Base drin; erst Requirements, flash-attn zuletzt
RUN pip install -r requirements.txt

# ---- FlashAttention robust installieren ----
# 1) Wheel versuchen; 2) Fallback auf Source-Build mit begrenzten Jobs
ENV MAX_JOBS=4
RUN pip install "flash-attn==2.5.9" --only-binary=:all: || \
    pip install "flash-attn==2.5.8" --no-build-isolation

# ---- Sanity-Check ----
RUN python - <<'PY'\n\
import torch, importlib\n\
print('Torch', torch.__version__, 'CUDA', torch.version.cuda, 'cuDNN', torch.backends.cudnn.version())\n\
print('flash_attn', importlib.import_module('flash_attn').__version__)\n\
assert torch.cuda.is_available()\n\
PY

# ---- Workspace ----
WORKDIR /workspace
ENV PYTHONPATH=/opt/Wan2.2:${PYTHONPATH}

EXPOSE 8000 8888

CMD ["bash", "start.sh"]