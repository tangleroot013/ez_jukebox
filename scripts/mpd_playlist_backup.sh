#!/usr/bin/env bash
# mpd_playlist_backup.sh – backup current playlist to ~/.mpd/backups/
set -euo pipefail

BACKUP_DIR="${HOME}/.mpd/backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="${BACKUP_DIR}/playlist_$(date +%F_%H%M%S).m3u"
mpc playlist > "$BACKUP_FILE"
echo "[ok] Playlist backed up to $BACKUP_FILE"
