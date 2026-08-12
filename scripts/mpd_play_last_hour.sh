#!/usr/bin/env bash
# mpd_play_last_hour.sh – play tracks added in the last hour
set -euo pipefail

mpc clear
mpc findadd modified-since "-1 hour"
mpc play
echo "[ok] Now playing tracks added in the last hour."
