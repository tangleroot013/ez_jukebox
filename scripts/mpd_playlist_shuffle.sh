#!/usr/bin/env bash
# mpd_playlist_shuffle.sh – shuffle the current playlist
set -euo pipefail

mpc random on
mpc consume off
mpc single off
mpc play
echo "[ok] Playlist shuffled and playback started."
