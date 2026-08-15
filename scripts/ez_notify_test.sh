#!/usr/bin/env bash
set -euo pipefail

SERVICE="ez-jukebox-notify.service"
OUT_FILE="$HOME/.local/share/ez_jukebox/now_playing.json"

echo "[ez_jukebox] notify-test starting..."
echo "[ez_jukebox] Restarting systemd user unit: $SERVICE"

systemctl --user restart "$SERVICE" >/dev/null || true

# Wait for OUT_FILE to exist
for _ in {1..20}; do
  if [ -f "$OUT_FILE" ]; then
    break
  fi
  sleep 0.2
done

if [ ! -f "$OUT_FILE" ]; then
  echo "[ez_jukebox] ❌ now_playing.json not found at: $OUT_FILE"
  echo "[ez_jukebox] Recent daemon logs:"
  journalctl --user -u "$SERVICE" -n 80 --no-pager || true
  exit 1
fi

# Record initial mtime
INITIAL_MTIME="$(stat -c %Y "$OUT_FILE" 2>/dev/null || echo 0)"

echo "[ez_jukebox] Waiting for now_playing.json to update..."
TIMEOUT_SECONDS=5
SLEEP_STEP=0.2
ELAPSED=0

while [ "$ELAPSED" -lt "$TIMEOUT_SECONDS" ]; do
  NEW_MTIME="$(stat -c %Y "$OUT_FILE" 2>/dev/null || echo 0)"
  if [ "$NEW_MTIME" -gt "$INITIAL_MTIME" ]; then
    echo "[ez_jukebox] ✅ now_playing.json updated."
    echo "[ez_jukebox] Payload (latest):"
    cat "$OUT_FILE"
    exit 0
  fi
  sleep "$SLEEP_STEP"
  ELAPSED="$(python3 - <<'PY'
import os
print(float(os.environ.get("ELAPSED","0")) + float(os.environ.get("SLEEP_STEP","0.2")))
PY
)"
done

echo "[ez_jukebox] ❌ Timeout waiting for now_playing.json update."
echo "[ez_jukebox] Recent daemon logs:"
journalctl --user -u "$SERVICE" -n 120 --no-pager || true
echo "[ez_jukebox] Payload (current):"
cat "$OUT_FILE" || true
exit 1
