#!/usr/bin/env bash
# mpd_web_ui_toggle.sh – toggle MPD’s built-in HTTP stream on/off
set -euo pipefail

CONF="${HOME}/.mpd/mpd.conf"
[[ -f "$CONF" ]] || { echo "[warn] ${CONF} not found."; exit 1; }

if grep -q '^bind_to_address "any"' "$CONF"; then
    sed -i 's/^bind_to_address "any"/bind_to_address "127.0.0.1"/' "$CONF"
    systemctl --user restart mpd
    echo "[ok] HTTP stream disabled (bind_to_address 127.0.0.1)."
else
    sed -i 's/^bind_to_address "127.0.0.1"/bind_to_address "any"/' "$CONF"
    systemctl --user restart mpd
    echo "[ok] HTTP stream enabled (bind_to_address any)."
fi
