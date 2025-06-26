#!/bin/bash

REMOTE_NAME="models-server"
REMOTE_PATH="${REMOTE_NAME}:"                   
MOUNT_POINT="/home/jovyan"
RCLONE_CONFIG="/workspace/config/rclone.conf"

mkdir -p "$MOUNT_POINT"

if mountpoint -q "$MOUNT_POINT"; then
    echo "✅ Bereits gemountet: $MOUNT_POINT"
else
    echo "⏳ Mounting $REMOTE_PATH to $MOUNT_POINT ..."
    rclone mount "$REMOTE_PATH" "$MOUNT_POINT" \
        --config "$RCLONE_CONFIG" \
        --allow-other \
        --dir-cache-time 1000h \
        --poll-interval 15s \
        --vfs-cache-mode full \
        --vfs-cache-max-age 336h \
        --vfs-read-chunk-size 64M \
        --vfs-read-chunk-size-limit 1G \
        --daemon

    echo "✅ Mount erfolgreich!"
fi

