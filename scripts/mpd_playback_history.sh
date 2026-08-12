#!/usr/bin/env bash
# mpd_playback_history.sh – show recently played tracks (last 20)
set -euo pipefail

mpc history | head -n 20 | nl -w 2 -s ' '
