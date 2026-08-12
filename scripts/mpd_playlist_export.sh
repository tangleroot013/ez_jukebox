#!/usr/bin/env bash
# mpd_playlist_export.sh – export current playlist to a file
set -euo pipefail

FILE="${1:-${HOME}/Music/mpd_playlist_$(date +%F_%H%M%S).m3u}"
mpc playlist > "$FILE"
echo "[ok] Playlist exported to $FILE"
