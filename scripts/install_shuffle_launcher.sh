#!/usr/bin/env bash
# install_shuffle_launcher.sh - install the .desktop shelf launcher
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[1/6] stopping the stuck tray process..."
pkill -f monitor_jukebox.py 2>/dev/null && echo "  -> killed running instance" || echo "  -> nothing running"

echo ""
echo "[2/6] generating shelf icon..."
mkdir -p assets
python3 - <<'PYEOF'
from pathlib import Path
from PIL import Image, ImageDraw

out = Path("assets/ez_jukebox_icon.png")
out.parent.mkdir(parents=True, exist_ok=True)

size = 128
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
draw.ellipse((4, 4, size - 4, size - 4), fill=(30, 30, 30, 255))
draw.ellipse((size * 0.25, size * 0.25, size * 0.75, size * 0.75), fill=(0, 200, 100, 255))
draw.line((size * 0.35, size * 0.4, size * 0.65, size * 0.6), fill=(255, 255, 255, 255), width=4)
draw.line((size * 0.35, size * 0.6, size * 0.65, size * 0.4), fill=(255, 255, 255, 255), width=4)
img.save(out)
print(f"[ok] {out}")
PYEOF

echo ""
echo "[3/6] installing shuffle wrapper script..."
cat > scripts/ez_jukebox_shuffle.sh <<'WRAP_EOF'
#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - start or advance the shelf player's managed queue
set -euo pipefail

DATA_DIR="${HOME}/.local/share/ez_jukebox"
LOG="${DATA_DIR}/shuffle.log"
STATE="${DATA_DIR}/shuffle-current"
PRELOAD=3
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

current="$(mpc current 2>/dev/null || true)"

if [[ -z "$current" || ! -s "$STATE" ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        exit 1
    fi
    mpc clear >/dev/null
    printf '%s\n' "${tracks[@]}" | while IFS= read -r track; do
        [[ -n "$track" ]] && mpc add "$track" >/dev/null
    done
    mpc random off >/dev/null
    mpc repeat off >/dev/null
    mpc play 1 >/dev/null
else
    mpc next >/dev/null
fi

position="$(mpc status | sed -n 's/.*#\([0-9][0-9]*\)\/[0-9][0-9]*.*/\1/p' | head -n 1)"
position="${position:-1}"
while [[ "$(mpc playlist | wc -l)" -lt "$((position + PRELOAD))" ]]; do
    track="$(mpc listall | shuf -n 1)"
    [[ -z "$track" ]] && break
    mpc add "$track" >/dev/null
done

current="$(mpc current 2>/dev/null || true)"
printf '%s' "$current" > "$STATE"
log "now playing: ${current:-none}; upcoming target: $PRELOAD"
WRAP_EOF
chmod +x scripts/ez_jukebox_shuffle.sh
echo "  -> scripts/ez_jukebox_shuffle.sh"

echo ""
echo "[4/6] installing .desktop launcher for the ChromeOS shelf..."
mkdir -p "${HOME}/.local/share/applications"
DESKTOP_FILE="${HOME}/.local/share/applications/ez-jukebox-shuffle.desktop"
cat > "$DESKTOP_FILE" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=ez_jukebox Shuffle
Comment=Shuffle and skip to a random track
Exec=${REPO_ROOT}/scripts/ez_jukebox_shuffle.sh
Icon=${REPO_ROOT}/assets/ez_jukebox_icon.png
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupNotify=false
DESKTOP_EOF
chmod +x "$DESKTOP_FILE"
echo "  -> $DESKTOP_FILE"

echo ""
echo "[5/6] refreshing desktop database..."
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "${HOME}/.local/share/applications" && echo "  -> refreshed"
else
    echo "  -> [skip] update-desktop-database not installed; ChromeOS usually picks it up within a few seconds regardless"
fi

echo ""
echo "=== Done ==="
echo "Find 'ez_jukebox Shuffle' in the ChromeOS app launcher (search or"
echo "all-apps view), then right-click -> Pin to shelf. No more stuck icon."
echo "Log at ~/.local/share/ez_jukebox/shuffle.log for troubleshooting."
