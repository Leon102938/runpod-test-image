#!/usr/bin/env bash
set -euo pipefail
command -v uuidgen >/dev/null 2>&1 || uuidgen(){ cat /proc/sys/kernel/random/uuid; }

# ins Repo wechseln & PYTHONPATH setzen
cd "$(dirname "$0")/.."
export PYTHONPATH=/workspace/ThinkSound:${PYTHONPATH:-}

# Args prüfen
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "Usage: $0 <video_path> <title> <description> [use-half]"
  exit 1
fi

VIDEO_PATH="$1"
TITLE="$2"
DESCRIPTION="$3"
USE_HALF_FLAG="${4:-}"

# Video muss existieren
if [ ! -f "$VIDEO_PATH" ]; then
  echo "❌ VIDEO_PATH not found: $VIDEO_PATH"
  exit 1
fi

mkdir -p videos cot_coarse results results/features

VIDEO_FILE="$(basename "$VIDEO_PATH")"
VIDEO_EXT="${VIDEO_FILE##*.}"
VIDEO_ID="${VIDEO_FILE%.*}"
TEMP_VIDEO_PATH="videos/demo.mp4"
CLEANUP_TEMP=0

# Wenn Quelle ≠ Ziel, kopieren (und sicherstellen, dass es da ist)
if [ "$(realpath -m "$VIDEO_PATH")" != "$(realpath -m "$TEMP_VIDEO_PATH")" ]; then
  cp -f "$VIDEO_PATH" "$TEMP_VIDEO_PATH"
fi
if [ ! -s "$TEMP_VIDEO_PATH" ]; then
  echo "❌ Temp video missing after copy: $TEMP_VIDEO_PATH"
  exit 2
fi

# Dauer bestimmen
DURATION="$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$TEMP_VIDEO_PATH" || true)"
DURATION_SEC="${DURATION%.*}"
if [ -z "${DURATION_SEC:-}" ]; then
  echo "❌ Could not read duration via ffprobe"
  exit 2
fi
echo "Duration is: $DURATION_SEC"

# CoT CSV schreiben
CAPTION_COT="$(echo "$DESCRIPTION" | tr '"' "'")"
CSV_PATH="cot_coarse/cot.csv"
echo "id,caption,caption_cot" > "$CSV_PATH"
echo "demo,$TITLE,\"$CAPTION_COT\"" >> "$CSV_PATH"

# Features extrahieren → immer in results/features
echo "⏳ Extracting features..."
EXTRACT_CMD=(python extract_latents.py --duration_sec "$DURATION_SEC" --save-dir results/features)
[ "$USE_HALF_FLAG" = "use-half" ] && EXTRACT_CMD+=(--use_half)
"${EXTRACT_CMD[@]}"

echo "⏳ Running model inference..."
HALF_FLAG=()
[ "$USE_HALF_FLAG" = "use-half" ] && HALF_FLAG=(--half)

python /workspace/ThinkSound/predict.py \
  --ckpt /workspace/ThinkSound/ckpts/thinksound.ckpt \
  --vae  /workspace/ThinkSound/ckpts/vae.ckpt \
  --features_dir /workspace/ThinkSound/results/features \
  --results-dir  /workspace/ThinkSound/results \
  --duration-sec "$DURATION_SEC" \
  --title "$TITLE" \
  --cot   "$DESCRIPTION" \
  ${HALF_FLAG[@]} 
  --ckpt /workspace/ThinkSound/ckpts/thinksound.ckpt 
  --vae /workspace/ThinkSound/ckpts/vae.ckpt 
  --synchformer /workspace/ThinkSound/ckpts/synchformer_state_dict.pth 
  --results-dir /workspace/ThinkSound/results 
  --duration-sec "$DURATION_SEC" 
  --title "$TITLE" 
  --cot "$DESCRIPTION" 
  $( [ "$USE_HALF_FLAG" = "use-half" ] python -u -m ThinkSound.inference.generation \python -u -m ThinkSound.inference.generation \ echo --half )
  --config      /workspace/ThinkSound/ThinkSound/configs/model_configs/thinksound.json \
  --ckpt        /workspace/ThinkSound/ckpts/thinksound.ckpt \
  --vae         /workspace/ThinkSound/ckpts/vae.ckpt \
  --synchformer /workspace/ThinkSound/ckpts/synchformer_state_dict.pth \
  --video       /workspace/ThinkSound/videos/demo.mp4 \
  --features_dir /workspace/ThinkSound/results/features \
  --save-dir     /workspace/ThinkSound/results \
  --title       "$TITLE" \
  --cot         "$DESCRIPTION" \
  "${HALF_FLAG[@]}"

# jüngstes Ergebnis finden (wav/mp3/mp4)
LATEST_FILE="$(find results /tmp -maxdepth 6 -type f \( -name '*.wav' -o -name '*.mp3' -o -name '*.mp4' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | cut -d' ' -f2-)"
if [ -z "${LATEST_FILE:-}" ]; then
  echo "❌ No output found (wav/mp3/mp4)"
  exit 5
fi

# Wenn MP4 ohne reine WAV: Audio extrahieren
AUDIO_PATH="$LATEST_FILE"
if [[ "$LATEST_FILE" == *.mp4 ]]; then
  echo "ℹ️ Found MP4 with embedded audio → extracting WAV..."
  ffmpeg -y -i "$LATEST_FILE" -vn -ac 1 -ar 44100 -acodec pcm_s16le "results/${VIDEO_ID}.wav" >/dev/null 2>&1
  AUDIO_PATH="results/${VIDEO_ID}.wav"
fi

if [ ! -f "$AUDIO_PATH" ]; then
  echo "❌ Generated audio file not found"
  exit 5
fi

# Aufräumen (nur temp MP4)
[ "$CLEANUP_TEMP" -eq 1 ] && rm -f "$TEMP_VIDEO_PATH"

echo "✅ Audio generated successfully!"
echo "Audio file path: $AUDIO_PATH"
