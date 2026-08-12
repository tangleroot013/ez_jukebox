#!/usr/bin/env bash
# crostini_audio_priority.sh – set higher priority for Crostini
set -euo pipefail

if grep -q "cros-termina" /proc/version; then
    ./scripts/boost_mpd_priority.sh --crostini
else
    echo "[info] Not running in Crostini – skipping."
fi
