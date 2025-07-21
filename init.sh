#!/bin/bash

source ./tools.config

download_if_missing() {
  local file_path="$1"
  local remote_url="$2"

  if [ -f "$file_path" ]; then
    echo "✅ $file_path bereits vorhanden – Download übersprungen."
  else
    echo "⬇️  Lade $remote_url nach $file_path ..."
    mkdir -p "$(dirname "$file_path")"

    if command -v aria2c >/dev/null 2>&1; then
      echo "🚀 aria2c erkannt – paralleler Download aktiv."
      aria2c -x 16 -s 16 -c -d "$(dirname "$file_path")" -o "$(basename "$file_path")" "$remote_url"
    else
      echo "⚠️  aria2c nicht gefunden – fallback auf wget."
      wget -nc -O "$file_path" "$remote_url"
    fi
  fi
}

# === TXT2IMG ===
if [ "$USE_TXT2IMG" == "on" ]; then
  echo "🔍 Starte TXT2IMG-Modell-Download ..."
  download_if_missing \
    "$TXT2IMG_PATH/$TXT2IMG_FILENAME" \
    "$BASE_URL/models/txt2img/$TXT2IMG_FILENAME"
  echo "✅ TXT2IMG-Setup abgeschlossen."
fi

# === IMG2VID ===
if [ "$USE_IMG2VID" == "on" ]; then
  echo "🎬 Starte IMG2VID-Modell-Download ($IMG2VID_MODEL) ..."

  TMP_ARIA_LIST="/tmp/aria2_img2vid.txt"
  rm -f "$TMP_ARIA_LIST"
  mkdir -p "$IMG2VID_PATH"

  for file in $IMG2VID_MODEL_FILES; do
    echo "$BASE_URL/ai-core/models/img2vid/$IMG2VID_MODEL/$file" >> "$TMP_ARIA_LIST"
  done

  if command -v aria2c >/dev/null 2>&1; then
    echo "🚀 Starte parallelen aria2c-Download für IMG2VID-Modell ..."
    aria2c -j 16 -x 16 -s 16 -c --allow-overwrite=true -d "$IMG2VID_PATH" -i "$TMP_ARIA_LIST"
  else
    echo "⚠️  aria2c nicht gefunden – fallback auf wget (nacheinander)."
    while read -r url; do
      file_name=$(basename "$url")
      echo "⬇️  Lade $file_name ..."
      wget -nc -O "$IMG2VID_PATH/$file_name" "$url"
    done < "$TMP_ARIA_LIST"
  fi

  echo "✅ IMG2VID-Setup abgeschlossen."
fi


