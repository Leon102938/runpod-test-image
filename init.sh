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



# ThinkSound – exakt dein DW
if [ "${ThinkSound}" = "on" ]; then
  echo "🎧 Lade ThinkSound (ckpts) ..."
  mkdir -p /workspace/ThinkSound/ckpts
  python - <<'PY'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="liuhuadai/ThinkSound",
    repo_type="model",
    local_dir="/workspace/ThinkSound/ckpts",
    local_dir_use_symlinks=False,
    resume_download=True,
)
print("OK")
PY
  echo "✅ ThinkSound fertig."
fi

echo "🏁 init done."
