#!/usr/bin/env bash
# mpd_play_fav.sh – play a user-curated “favorites” playlist
set -euo pipefail

FAV_FILE="${HOME}/.mpd/favorites.m3u"
[[ -f "$FAV_FILE" ]] || { echo "[warn] ${FAV_FILE} not found – create it first."; exit 1; }

mpc clear
mpc load "$FAV_FILE"
mpc play
echo "[ok] Now playing favorites playlist."
