#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="$HOME/.local/share/ez_jukebox/now_playing.json"
SERVICE="ez-jukebox-notify.service"

echo "[ez_jukebox] notify-test starting..."
echo "[ez_jukebox] Restarting systemd user unit: $SERVICE"

INITIAL_MTIME="$(stat -c %Y "$OUT_FILE" 2>/dev/null || echo 0)"

systemctl --user restart "$SERVICE"

echo "[ez_jukebox] Waiting for now_playing.json to update..."
TIMEOUT_MS=5000
SLEEP_MS=200
ELAPSED_MS=0

while [ "$ELAPSED_MS" -lt "$TIMEOUT_MS" ]; do
    NEW_MTIME="$(stat -c %Y "$OUT_FILE" 2>/dev/null || echo 0)"
    if [ "$NEW_MTIME" -gt "$INITIAL_MTIME" ]; then
        echo "[ez_jukebox] ✅ now_playing.json updated successfully."
        echo "[ez_jukebox] Payload (latest):"
        cat "$OUT_FILE"
        exit 0
    fi
    sleep 0.2
    ELAPSED_MS=$((ELAPSED_MS + SLEEP_MS))
done

echo "[ez_jukebox] ❌ Timeout waiting for now_playing.json update."
echo "[ez_jukebox] Recent daemon logs:"
journalctl --user -u "$SERVICE" -n 120 --no-pager || true
echo "[ez_jukebox] Payload (current):"
cat "$OUT_FILE" || true
exit 1
