#!/usr/bin/env bash
# ==============================================================================
# Application Launcher Entrypoint
# ==============================================================================
set -e

# Clear screen for clean presentation
clear

# Render quick hint reference
python3 scripts/show_hints.py

# Ensure underlying MPD service is running
if ! systemctl --user is-active --quiet mpd; then
    echo -e "\033[33m⚠️ MPD user service is inactive. Starting MPD...\033[0m"
    systemctl --user start mpd
fi

echo -e "\033[32m✅ Service status verified. System ready.\033[0m\n"
