#!/usr/bin/env bash
# tune_audio_buffer.sh – adjust MPD buffer based on battery state
set -euo pipefail

BATTERY_STATE=$(upower -i /org/freedesktop/UPower/devices/battery_BAT0 | grep "state:" | awk '{print $2}')
BUFFER_SIZE=${1:-32768}  # default: 32768

if [[ "$BATTERY_STATE" == "discharging" ]]; then
    BUFFER_SIZE=16384
fi

./bin/jukebox tune --buffer-kb "$BUFFER_SIZE" --apply
echo "[ok] Audio buffer set to $BUFFER_SIZE KB (battery: $BATTERY_STATE)"
