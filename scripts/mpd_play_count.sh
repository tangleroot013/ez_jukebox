#!/usr/bin/env bash
# mpd_play_count.sh – show how many tracks are in the queue
set -euo pipefail

COUNT=$(mpc playlist | wc -l)
echo "[info] MPD queue contains $COUNT track(s)."
