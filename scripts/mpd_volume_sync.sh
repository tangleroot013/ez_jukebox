#!/usr/bin/env bash
# mpd_volume_sync.sh – sync MPD volume to PulseAudio volume
set -euo pipefail

PA_VOL=$(pactl get-sink-volume @DEFAULT_SINK@ | awk -F' ' '/Volume:/ {print $5}' | tr -d '%')
mpc volume "$PA_VOL"

echo "[ok] MPD volume synced to PulseAudio: $PA_VOL%"
