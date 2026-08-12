#!/usr/bin/env bash
# mpd_play_starred.sh – play only tracks tagged ★ in your library
set -euo pipefail

STAR_DIR="${HOME}/Music/★"
[[ -d "$STAR_DIR" ]] || { echo "[warn] ${STAR_DIR} not found – create it first."; exit 1; }

mpc clear
mpc add "$STAR_DIR"
mpc play
echo "[ok] Now playing ★-tagged tracks."
