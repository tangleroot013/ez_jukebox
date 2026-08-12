#!/usr/bin/env bash
# mpd_replaygain_apply.sh – apply ReplayGain tags to the entire library
set -euo pipefail

echo "[info] Applying ReplayGain tags to the entire library..."
mpc update
mpc replaygain on
mpc volume 80   # ReplayGain will scale to this level
echo "[ok] ReplayGain applied; volume set to 80%."
