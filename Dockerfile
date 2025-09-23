# ✅ CUDA 12.1.1 + cuDNN + Ubuntu 22.04 (glibc 2.35) to avoid GLIBC_2.32 errors
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Berlin

# ---- System deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3.11 python3.11-venv python3.11-dev \
    git git-lfs curl wget unzip ca-certificates \
    ffmpeg libsndfile1 libsentencepiece-dev \
    tzdata nano tmux aria2 rclone fuse \
    && update-ca-certificates \
    && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
    && dpkg-reconfigure -f noninteractive tzdata \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# ---- Create venv ----
ENV VENV=/opt/venv
RUN python3.11 -m venv ${VENV}
ENV PATH="${VENV}/bin:${PATH}"

# ---- Upgrade pip/setuptools/wheel ----
RUN python -m pip install --upgrade pip setuptools wheel

# ---- CUDA env (help some builds) ----
ENV CUDA_HOME=/usr/local/cuda \
    TORCH_CUDA_ARCH_LIST="8.9" \
    MAX_JOBS=8

# ---- HuggingFace caches ----
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# ---- Pin a proven working stack for Wan2.2 on 4090 (CUDA 12.1) ----
# Torch stack
RUN pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121

# Core scientific stack (NumPy < 2 for SciPy/Numba, ABI-stable)
RUN pip install numpy==1.26.4 scipy==1.11.4 numba==0.61.2 pandas pyarrow

# HF & diffusion ecosystem (API-compatible versions)
RUN pip install diffusers==0.30.2 transformers==4.41.2 peft==0.11.1 accelerate==0.31.0 \
    tokenizers==0.15.2 safetensors>=0.4.4 \
    sentencepiece==0.1.99 protobuf==4.25.3

# Media & utils
RUN pip install opencv-python imageio[ffmpeg] imageio-ffmpeg decord \
    tqdm easydict ftfy omegaconf hydra-core lightning rich gdown wget GitPython

# ---- FlashAttention: on Ubuntu 22.04 we can often use wheels; pin a compatible version ----
# If a wheel fails for your GPU/CUDA combo, fallback to building from source (uncomment second line).
RUN pip install flash-attn==2.5.9 --only-binary=:all: || \
    pip install flash-attn==2.5.8 --no-build-isolation

# ---- Project workspace ----
WORKDIR /workspace
# (Copy later or mount at runtime. If you must bake in the repo, uncomment the next line)
# COPY . .

# Helpful runtime envs
ENV TRANSFORMERS_NO_FAST_TOKENIZER=1 \
    TOKENIZERS_PARALLELISM=false

# Expose common ports for notebooks / APIs
EXPOSE 8000 8888

# Default shell
CMD ["/bin/bash"]
