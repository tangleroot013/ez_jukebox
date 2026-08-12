#!/usr/bin/env bash
# mpd_log_level.sh – toggle MPD debug logging
set -euo pipefail

LOG_FILE="${HOME}/.mpd/mpd.log"
if [[ -f "$LOG_FILE" ]]; then
    rm -f "$LOG_FILE"
    echo "[ok] MPD debug logging disabled."
else
    touch "$LOG_FILE"
    systemctl --user restart mpd
    echo "[ok] MPD debug logging enabled – restarting MPD."
fi
