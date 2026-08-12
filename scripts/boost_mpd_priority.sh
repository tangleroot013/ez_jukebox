#!/bin/bash
# boost_mpd_priority.sh
# Creates a systemd override for the user's MPD service to give it
# higher CPU and I/O priority, preventing browsers from starving the audio thread.

set -euo pipefail

OVERRIDE_DIR="${HOME}/.config/systemd/user/mpd.service.d"
OVERRIDE_FILE="${OVERRIDE_DIR}/priority-override.conf"

echo "[info] Creating systemd override directory for MPD..."
mkdir -p "$OVERRIDE_DIR"

echo "[info] Writing CPU & I/O priority rules..."
cat <<'CONFIG_EOF' > "$OVERRIDE_FILE"
[Service]
# Give MPD a slightly higher CPU priority than standard user apps (like browsers)
Nice=-5

# Request Realtime Audio Scheduling (if permitted by system audio group)
LimitRTPRIO=50
LimitRTTIME=infinity

# Set I/O Scheduling to Realtime (Class 1) to bypass heavy disk usage from browsers
IOSchedulingClass=realtime
IOSchedulingPriority=4
CONFIG_EOF

echo "[ok] Wrote override to $OVERRIDE_FILE"

echo "[info] Reloading systemd user daemon and restarting MPD..."
systemctl --user daemon-reload
systemctl --user restart mpd || echo "[warn] MPD restart failed - is it running via systemd?"

echo "[done] MPD is now running with audiophile priority."
