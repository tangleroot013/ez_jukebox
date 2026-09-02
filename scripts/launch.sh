#!/usr/bin/env bash
# ==============================================================================
# Application Launcher Entrypoint
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clear screen for clean presentation
clear

# Render quick hint reference
python3 "$SCRIPT_DIR/show_hints.py"

# Ensure underlying MPD service is running
if ! systemctl --user is-active --quiet mpd; then
    echo -e "\033[33m⚠️ MPD user service is inactive. Starting MPD...\033[0m"
    systemctl --user start mpd
fi

echo -e "\033[32m✅ Service status verified. System ready.\033[0m\n"

echo "🚀 Starting tray monitor..."
python3 "$SCRIPT_DIR/monitor_jukebox.py" &
