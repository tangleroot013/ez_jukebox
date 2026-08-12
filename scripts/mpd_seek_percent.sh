#!/usr/bin/env bash
# mpd_seek_percent.sh – seek to a percentage of the current track
set -euo pipefail

PERCENT="${1:-50}"   # default: 50 %
[[ "$PERCENT" =~ ^[0-9]+$ ]] || { echo "usage: ./mpd_seek_percent.sh <0-100>"; exit 1; }

mpc seek "$PERCENT"
echo "[ok] Seeking to $PERCENT % of current track."
