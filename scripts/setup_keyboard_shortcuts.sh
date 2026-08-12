#!/usr/bin/env bash
# setup_keyboard_shortcuts.sh – bind media keys to mpc
set -euo pipefail

mkdir -p ~/.config/sway
cat <<'SWAY_EOF' > ~/.config/sway/config
bindsym XF86AudioPlay exec mpc toggle
bindsym XF86AudioNext exec mpc next
bindsym XF86AudioPrev exec mpc prev
SWAY_EOF

swaymsg reload
echo "[ok] Media key shortcuts configured."
