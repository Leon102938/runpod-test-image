# ✅ CUDA 12.1.1 + cuDNN8 + Ubuntu 22.04 (glibc 2.35)
FROM nvidia/cuda:12.1.1-cudnn9-devel-ubuntu22.04

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
    nano tmux aria2 rclone fuse tzdata \
 && update-ca-certificates \
 && ln -fs /usr/share/zoneinfo/${TZ} /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata \
 && git lfs install \
 && rm -rf /var/lib/apt/lists/*

# ---- venv ----
ENV VENV=/opt/venv
RUN python3.11 -m venv ${VENV}
ENV PATH="${VENV}/bin:${PATH}"

# ---- pip basics ----
RUN python -m pip install --upgrade pip setuptools wheel

# ---- CUDA build env ----
ENV CUDA_HOME=/usr/local/cuda \
    TORCH_CUDA_ARCH_LIST="8.9" \
    MAX_JOBS=8

# ---- HF caches ----
ENV HF_HOME=/workspace/.cache/huggingface \
    TRANSFORMERS_CACHE=/workspace/.cache/huggingface/transformers \
    HF_HUB_CACHE=/workspace/.cache/huggingface/hub

# ---- Torch stack (CUDA 12.1) ----
RUN pip install --extra-index-url https://download.pytorch.org/whl/cu121 \
    torch==2.4.0+cu121 torchvision==0.19.0+cu121 torchaudio==2.4.0+cu121

# ---- Scientific core (NumPy < 2) ----
RUN pip install numpy==1.26.4 scipy==1.11.4 numba==0.61.2 pandas pyarrow

# ---- Diffusion / HF ecosystem (API-stable pins) ----
RUN pip install diffusers==0.30.2 peft==0.11.1 accelerate==0.31.0 safetensors>=0.4.4 \
    sentencepiece==0.1.99 protobuf==4.25.3

# transformers + tokenizers (zueinander passend)
RUN pip install transformers==4.40.2 tokenizers==0.19.1

# ---- Media & utils ----
RUN pip install opencv-python imageio[ffmpeg] imageio-ffmpeg decord \
    tqdm easydict ftfy omegaconf hydra-core lightning rich gdown wget GitPython

# ---- FlashAttention: zuerst Wheel, sonst Fallback Source-Build ----
RUN pip install flash-attn==2.5.9 --only-binary=:all: || \
    pip install flash-attn==2.5.8 --no-build-isolation

# ---- Runtime envs ----
ENV TRANSFORMERS_NO_FAST_TOKENIZER=1 \
    TOKENIZERS_PARALLELISM=false

# ---- Workspace ----
WORKDIR /workspace
# COPY . .   # falls du das Repo ins Image backen willst

EXPOSE 8000 8888
CMD ["bash", "start.sh"]