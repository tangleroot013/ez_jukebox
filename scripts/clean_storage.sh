#!/usr/bin/env bash
# clean_storage.sh – clean cache and old backups when disk is low
set -euo pipefail

FREE_SPACE=$(df -h / | awk 'NR==2 {print $4}' | tr -d 'G')
if [[ "$FREE_SPACE" =~ ^[0-9]+$ ]] && (( FREE_SPACE < 10 )); then
    echo "[info] Low disk space ($FREE_SPACE GB free) – cleaning cache..."
    rm -rf ~/.cache/mpd/*
    find ~/.mpd/backups -type f -mtime +7 -delete
    echo "[ok] Cleaned cache and old backups."
else
    echo "[info] Disk space OK ($FREE_SPACE GB free)."
fi
