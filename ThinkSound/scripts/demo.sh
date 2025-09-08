#!/usr/bin/env bash
# Usage: scripts/demo.sh <video_path> <title> <description> [use-half]
# ENV (optional): HF_HOME, TORCH_HOME, THINKSOUND_CKPT, THINKSOUND_VAE, THINKSOUND_SYNCHFORMER, CFG, STEPS
set -euo pipefail

die(){ echo "❌ $*" >&2; exit 1; }
need(){ command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"; }

# repo-root & PYTHONPATH
cd "$(dirname "$0")/.."
export PYTHONPATH="/workspace/ThinkSound${PYTHONPATH:+:$PYTHONPATH}"

# caches (overridable)
export HF_HOME="${HF_HOME:-/workspace/.cache/huggingface}"
export TORCH_HOME="${TORCH_HOME:-/workspace/.cache/torch}"
mkdir -p "$HF_HOME" "$TORCH_HOME"

need python; need ffprobe; need ffmpeg

# args
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "Usage: $0 <video_path> <title> <description> [use-half]"; exit 1
fi
VIDEO_PATH="$1"; TITLE="$2"; DESCRIPTION="$3"; USE_HALF_FLAG="${4:-}"

[ -f "$VIDEO_PATH" ] || die "VIDEO_PATH not found: $VIDEO_PATH"

# checkpoints (overridable)
CKPT="${THINKSOUND_CKPT:-/workspace/ThinkSound/ckpts/thinksound.ckpt}"
VAE="${THINKSOUND_VAE:-/workspace/ThinkSound/ckpts/vae.ckpt}"
SYNCH="${THINKSOUND_SYNCHFORMER:-/workspace/ThinkSound/ckpts/synchformer_state_dict.pth}"
[ -f "$CKPT" ] || die "Missing checkpoint: $CKPT"
[ -f "$VAE"  ] || die "Missing VAE: $VAE"

# default inference params (overridable via ENV)
CFG_VAL="${CFG:-2.8}"
STEPS_VAL="${STEPS:-48}"

mkdir -p videos cot_coarse results results/features

VIDEO_FILE="$(basename "$VIDEO_PATH")"
VIDEO_EXT="${VIDEO_FILE##*.}"
VIDEO_ID="${VIDEO_FILE%.*}"
TEMP_VIDEO_PATH="videos/${VIDEO_ID}.${VIDEO_EXT}"

# copy into ./videos if needed
if [ "$(realpath -m "$VIDEO_PATH")" != "$(realpath -m "$TEMP_VIDEO_PATH")" ]; then
  cp -f "$VIDEO_PATH" "$TEMP_VIDEO_PATH"
fi
[ -s "$TEMP_VIDEO_PATH" ] || die "Temp video missing after copy: $TEMP_VIDEO_PATH"

# duration
DURATION_RAW="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_VIDEO_PATH" || true)"
DURATION_SEC="${DURATION_RAW%.*}"
[ -n "${DURATION_SEC:-}" ] || die "Could not read duration via ffprobe"
echo "Duration is: $DURATION_SEC"

# CoT CSV for extractor
CAPTION_COT="$(printf '%s' "$DESCRIPTION" | tr '"' "'")"
CSV_PATH="cot_coarse/cot.csv"
{
  echo "id,caption,caption_cot"
  printf '%s,%s,"%s"\n' "$VIDEO_ID" "$TITLE" "$CAPTION_COT"
} > "$CSV_PATH"

# feature extraction
echo "⏳ Extracting features..."
EXTRACT_CMD=(python extract_latents.py --duration_sec "$DURATION_SEC" --save-dir results/features)
[ "${USE_HALF_FLAG:-}" = "use-half" ] && EXTRACT_CMD+=(--use_half)
"${EXTRACT_CMD[@]}"

# inference
echo "⏳ Running model inference..."
PREDICT_CMD=(python /workspace/ThinkSound/predict.py
  --ckpt         "$CKPT"
  --vae          "$VAE"
  --features_dir /workspace/ThinkSound/results/features
  --results-dir  /workspace/ThinkSound/results
  --duration-sec "$DURATION_SEC"
  --title        "$TITLE"
  --cot          "$DESCRIPTION"
  --features-id  "$VIDEO_ID"
  --cfg          "$CFG_VAL"
  --steps        "$STEPS_VAL"
  --no_video_cond

)
[ -f "$SYNCH" ] && PREDICT_CMD+=(--synchformer "$SYNCH")
[ "${USE_HALF_FLAG:-}" = "use-half" ] && PREDICT_CMD+=(--half)
"${PREDICT_CMD[@]}"

# find newest artifact (with fallback)
LATEST_FILE="$(find results /tmp -maxdepth 6 -type f \( -iname '*.wav' -o -iname '*.mp3' -o -iname '*.mp4' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2- || true)"
if [ -z "${LATEST_FILE:-}" ]; then
  LATEST_FILE="$(ls -t results/* 2>/dev/null | head -n1 || true)"
fi
[ -n "${LATEST_FILE:-}" ] || die "No output found (wav/mp3/mp4)"

# if mp4, extract wav
AUDIO_PATH="$LATEST_FILE"
if [[ "$LATEST_FILE" == *.mp4 ]]; then
  echo "ℹ️ MP4 detected → extracting WAV..."
  AUDIO_PATH="results/${VIDEO_ID}.wav"
  ffmpeg -y -i "$LATEST_FILE" -vn -ac 1 -ar 44100 -acodec pcm_s16le "$AUDIO_PATH" >/dev/null 2>&1
fi
[ -f "$AUDIO_PATH" ] || die "Generated audio file not found"

echo "✅ Audio generated successfully!"
echo "Audio file path: $AUDIO_PATH"
