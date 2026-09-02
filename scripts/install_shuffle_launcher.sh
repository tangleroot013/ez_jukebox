#!/usr/bin/env bash
# install_shuffle_launcher.sh - install the .desktop shelf launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/ez_jukebox"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install the EZ Jukebox shuffle launcher into the local application menu.

Options:
  -h, --help        Show this help
EOF
}

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
    "")
        ;;
    *)
        echo "Error: unknown option '$1'. Use --help for usage." >&2
        exit 2
        ;;
esac

echo "[1/5] stopping the old tray process..."
pkill -f monitor_jukebox.py 2>/dev/null && echo "  -> killed running instance" || echo "  -> nothing running"

echo ""
echo "[2/5] installing shelf icon..."
mkdir -p "$ICON_DIR"
mkdir -p "$CONFIG_DIR"
if [[ -f "$SCRIPT_DIR/../assets/ez_jukebox_icon.png" ]]; then
    cp "$SCRIPT_DIR/../assets/ez_jukebox_icon.png" "$ICON_DIR/ez_jukebox_icon.png"
    echo "  -> $ICON_DIR/ez_jukebox_icon.png"
else
    echo "  -> [warn] source icon not found; desktop entry will still be installed"
fi

echo ""
echo "[3/5] enabling shuffle launcher..."
chmod +x "$SCRIPT_DIR/ez_jukebox_shuffle.sh"
echo "  -> $SCRIPT_DIR/ez_jukebox_shuffle.sh"

echo ""
echo "[4/5] installing .desktop launcher..."
mkdir -p "$APP_DIR"
DESKTOP_FILE="$APP_DIR/ez_jukebox_shuffle.desktop"
cat > "$DESKTOP_FILE" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=ez_jukebox Shuffle
Comment=Launch background shuffle playback or skip to the next random track
Exec="${SCRIPT_DIR}/ez_jukebox_shuffle.sh"
Icon=${ICON_DIR}/ez_jukebox_icon.png
Terminal=false
Categories=Audio;Music;Player;
StartupNotify=false
DESKTOP_EOF
chmod +x "$DESKTOP_FILE"
echo "  -> $DESKTOP_FILE"

echo ""
echo "[5/5] refreshing desktop database..."
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" && echo "  -> refreshed"
else
    echo "  -> [skip] update-desktop-database not installed; ChromeOS usually picks it up within a few seconds regardless"
fi

echo ""
echo "=== Done ==="
echo "Find 'ez_jukebox Shuffle' in the application menu (search or"
echo "all-apps view), then right-click -> Pin to shelf. No more stuck icon."
echo "Log at ~/.local/share/ez_jukebox/shuffle.log for troubleshooting."
