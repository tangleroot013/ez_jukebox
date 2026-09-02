#!/usr/bin/env bash
# ez_jukebox_queue_watch.sh - maintain shuffle lookahead on MPD player events
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while :; do
    if mpc idle player >/dev/null 2>&1; then
        "$SCRIPT_DIR/ez_jukebox_shuffle.sh" --refill || true
    else
        sleep 3
    fi
done