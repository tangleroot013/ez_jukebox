#!/usr/bin/env bash
# power_button_hook.sh – pause MPD on power button press
set -euo pipefail

mpc pause
echo "[ok] MPD paused on power button press."
