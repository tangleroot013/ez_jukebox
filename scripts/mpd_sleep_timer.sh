#!/usr/bin/env bash
# mpd_sleep_timer.sh – pause playback after N minutes
set -euo pipefail

MINUTES="${1:-30}"   # default: 30 minutes
[[ "$MINUTES" =~ ^[0-9]+$ ]] || { echo "usage: ./mpd_sleep_timer.sh <minutes>"; exit 1; }

(
    sleep "$(( MINUTES * 60 ))"
    mpc pause
    echo "[ok] Sleep timer reached – playback paused."
) & disown
echo "[info] Sleep timer set for $MINUTES minutes."
