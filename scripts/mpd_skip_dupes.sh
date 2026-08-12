#!/usr/bin/env bash
# mpd_skip_dupes.sh – skip duplicate tracks in the queue
set -euo pipefail

TMP=$(mktemp)
mpc playlist | awk '!seen[$0]++' > "$TMP"
mpc clear
mpc load "$TMP"
rm -f "$TMP"
mpc play
echo "[ok] Duplicates removed; queue cleaned."
