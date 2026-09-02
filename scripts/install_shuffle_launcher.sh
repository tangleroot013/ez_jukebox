#!/usr/bin/env bash
# install_shuffle_launcher.sh - install the .desktop shelf launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons"

echo "[1/5] stopping the old tray process..."
pkill -f monitor_jukebox.py 2>/dev/null && echo "  -> killed running instance" || echo "  -> nothing running"

echo ""
echo "[2/5] installing shelf icon..."
mkdir -p "$ICON_DIR"
if [[ -f "$SCRIPT_DIR/../assets/ez_jukebox_icon.png" ]]; then
    cp "$SCRIPT_DIR/../assets/ez_jukebox_icon.png" "$ICON_DIR/ez_jukebox_icon.png"
    echo "  -> $ICON_DIR/ez_jukebox_icon.png"
else
    echo "  -> [warn] source icon not found; desktop entry will still be installed"
fi

echo ""
echo "[3/5] installing shuffle wrapper script..."
cat > "$SCRIPT_DIR/ez_jukebox_shuffle.sh" <<'WRAP_EOF'
#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - start or advance the shelf player's managed queue
set -euo pipefail

DATA_DIR="${HOME}/.local/share/ez_jukebox"
LOG="${DATA_DIR}/shuffle.log"
PRELOAD_COUNT=3
mkdir -p "$DATA_DIR"

log() {
    printf '%s: %s\n' "$(date)" "$*" >> "$LOG"
}

if ! command -v mpc >/dev/null 2>&1; then
    log "[error] mpc not found"
    exit 1
fi

if ! mpc status >/dev/null 2>&1; then
    log "[warn] MPD not responding -- restarting"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi

current_pos="$(mpc current -f '%position%' 2>/dev/null || true)"
queue_len="$(mpc playlist 2>/dev/null | wc -l)"

if [[ -z "$current_pos" || "$queue_len" -eq 0 ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD_COUNT + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        exit 1
    fi
    mpc -q clear
    mpc -q random off
    for track in "${tracks[@]}"; do
        [[ -n "$track" ]] && mpc -q add "$track"
    done
    mpc -q play 1
else
    mpc -q next
    current_pos=$((current_pos + 1))
    upcoming=$((queue_len - current_pos))
    needed=$((PRELOAD_COUNT - upcoming))
    for ((index = 0; index < needed; index++)); do
        track="$(mpc listall | shuf -n 1)"
        [[ -n "$track" ]] && mpc -q add "$track"
    done
fi

log "now playing: $(mpc current 2>/dev/null || true); upcoming target: $PRELOAD_COUNT"
WRAP_EOF
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
Exec=${SCRIPT_DIR}/ez_jukebox_shuffle.sh
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
