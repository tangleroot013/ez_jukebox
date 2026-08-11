#!/bin/bash
# Lyrics Watcher: Event-driven lyric fetcher on track changes
# Uses mpc idle player for 0% CPU idle wait; socket reconnect with fallback

set -euo pipefail

MUSIC_MGR="${HOME}/music_mgr.sh"
LYRICS_DIR="${HOME}/.lyrics"

mkdir -p "$LYRICS_DIR"

main_loop() {
    while true; do
        # Wait for player state change (0% CPU during idle)
        if mpc idle player 2>/dev/null | grep -q "player"; then
            # Track changed; fetch lyrics for current song
            "$MUSIC_MGR" lyrics > "${LYRICS_DIR}/.current" 2>/dev/null || true
            # Small delay to avoid thrashing
            sleep 1
        fi
    done
}

# Trap socket disconnect and reconnect
trap 'main_loop' SIGPIPE

main_loop
