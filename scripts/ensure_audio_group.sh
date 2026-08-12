#!/usr/bin/env bash
# ensure_audio_group.sh – ensure user is in the audio group
set -euo pipefail

if ! groups | grep -q "audio"; then
    sudo usermod -aG audio "$USER"
    echo "[ok] Added $USER to audio group. Reboot required."
else
    echo "[info] $USER is already in the audio group."
fi
