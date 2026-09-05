#!/usr/bin/env bash
set -euo pipefail
systemctl --user stop ez-jukebox-watcher.service 2>/dev/null || true
mpc stop 2>/dev/null || true
pkill -f mpd 2>/dev/null || true
pkill -f ncmpcpp 2>/dev/null || true
notify-send "ez_jukebox" "Stopped (watcher + player)" 2>/dev/null || true
