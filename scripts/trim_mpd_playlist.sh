#!/usr/bin/env bash
# trim_mpd_playlist.sh – keep only the last N tracks in MPD’s queue
set -euo pipefail

N=${1:-10}   # default: keep last 10 tracks

mpc playlist | tail -n "$N" | mpc clear
mpc load -
mpc play

echo "[ok] Playlist trimmed to last $N tracks."
