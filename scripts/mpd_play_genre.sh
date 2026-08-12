#!/usr/bin/env bash
# mpd_play_genre.sh – play a specific genre
set -euo pipefail

GENRE="${1:-rock}"   # default genre
mpc clear
mpc findadd genre "$GENRE"
mpc play
echo "[ok] Now playing genre: $GENRE"
