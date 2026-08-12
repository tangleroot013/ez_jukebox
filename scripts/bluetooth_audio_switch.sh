#!/usr/bin/env bash
# ==============================================================================
# ez_jukebox - Bluetooth Auto-Connect & Audio Switch
# ==============================================================================
set -euo pipefail

# Ensure target directory exists
mkdir -p "$(dirname "$0")"

# Check dependencies
if ! command -v pactl >/dev/null 2>&1; then
    echo "[!] Installing pulseaudio-utils..."
    sudo apt update && sudo apt install -y pulseaudio-utils
fi

sleep 1

# Detect connected Bluetooth A2DP audio sink
SINK=$(pactl list sinks short 2>/dev/null | grep "bluez_sink" | grep -i "a2dp" | head -n1 | awk '{print $2}')

if [[ -n "${SINK}" ]]; then
    echo "[+] Bluetooth A2DP sink detected: ${SINK}"
    pactl set-default-sink "${SINK}"
    echo "[+] Default audio output switched to Bluetooth."
    mpc stop >/dev/null 2>&1 || true
    mpc play >/dev/null 2>&1 || true
else
    echo "[i] No Bluetooth A2DP audio sink detected. Keeping default PulseAudio / CRAS output."
fi
