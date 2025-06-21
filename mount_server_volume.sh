#!/bin/bash

# Mountet dein lokales Server-Volume via Rclone (nur wenn noch nicht gemountet)
REMOTE_NAME="server-volume"
MOUNT_POINT="/workspace"

# Prüfen, ob es schon gemountet ist
if mountpoint -q "$MOUNT_POINT"; then
  echo "[RCLONE] $MOUNT_POINT ist bereits gemountet."
else
  echo "[RCLONE] Mounting $REMOTE_NAME to $MOUNT_POINT ..."
  mkdir -p "$MOUNT_POINT"
  rclone mount "$REMOTE_NAME":"$MOUNT_POINT" "$MOUNT_POINT" --allow-other --daemon
fi
