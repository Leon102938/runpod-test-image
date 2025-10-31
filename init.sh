#!/bin/bash
# super simple init: lädt nur Wan2.2 TI2V-5B nach /workspace/Wan2.2

# optional: Schalter aus tools.config (falls vorhanden)
source ./tools.config 2>/dev/null || true

if [ "${Wan22}" = "on" ]; then
  echo "📹 Lade Wan2.2 TI2V-5B ..."
  mkdir -p /workspace/Wan2.2

  huggingface-cli download Wan-AI/Wan2.2-TI2V-5B \
    --local-dir /workspace/Wan2.2/Wan2.2-TI2V-5B \
    --local-dir-use-symlinks False \
    --resume-download

  echo "✅ Wan2.2 Download fertig."
fi




