#!/usr/bin/env bash
# mpd_play_random.sh – play a random album
set -euo pipefail

ALBUM=$(mpc list album | shuf -n 1)
mpc clear
mpc findadd album "$ALBUM"
mpc play

echo "[ok] Now playing random album: $ALBUM"
