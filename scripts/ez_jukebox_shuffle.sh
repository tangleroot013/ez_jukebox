#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - one-shot shuffle+skip; run by the shelf launcher
set -uo pipefail
LOG="${HOME}/.local/share/ez_jukebox/shuffle.log"
mkdir -p "$(dirname "$LOG")"

if ! command -v mpc >/dev/null 2>&1; then
    echo "$(date): [error] mpc not found" >> "$LOG"
    exit 1
fi

if ! mpc status >/dev/null 2>&1; then
    echo "$(date): [warn] MPD not responding -- restarting" >> "$LOG"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi

mpc random on  >> "$LOG" 2>&1
mpc next       >> "$LOG" 2>&1
echo "$(date): shuffled -- now playing: $(mpc current 2>/dev/null)" >> "$LOG"
