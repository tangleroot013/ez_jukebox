#!/usr/bin/env bash
# mpd_playlist_import.sh – import a saved playlist
set -euo pipefail

FILE="${1:-}"
[[ -z "$FILE" || ! -f "$FILE" ]] && { echo "usage: ./mpd_playlist_import.sh <playlist.m3u>"; exit 1; }

mpc clear
mpc load "$FILE"
mpc play
echo "[ok] Playlist imported and now playing."
