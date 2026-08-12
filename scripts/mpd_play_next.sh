#!/usr/bin/env bash
# mpd_play_next.sh – enqueue a file/dir and start playback immediately
set -euo pipefail

TARGET="${1:-}"   # file or directory path
[[ -z "$TARGET" ]] && { echo "usage: ./mpd_play_next.sh <file|dir>"; exit 1; }

if [[ -d "$TARGET" ]]; then
    mpc clear
    mpc add "$TARGET"
else
    mpc clear
    mpc add "$TARGET"
fi

mpc play
echo "[ok] Now playing: $TARGET"
