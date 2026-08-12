#!/usr/bin/env bash
# mpd_auto_update.sh – update MPD DB if new files are detected
set -euo pipefail

MUSIC_DIR="${HOME}/Music"
DB_FILE="${HOME}/.mpd/database"

CURRENT_HASH=$(find "$MUSIC_DIR" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1)

if [[ -f "${DB_FILE}.last_hash" ]]; then
    LAST_HASH=$(cat "${DB_FILE}.last_hash")
    [[ "$CURRENT_HASH" == "$LAST_HASH" ]] && { echo "[info] No new files detected – skipping update."; exit 0; }
fi

echo "[info] New files detected – updating MPD database..."
mpc update
echo "$CURRENT_HASH" > "${DB_FILE}.last_hash"
echo "[ok] MPD database updated."
