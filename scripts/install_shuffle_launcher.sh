#!/usr/bin/env bash
# install_shuffle_launcher.sh - replace the crashing GTK tray icon with a
# stateless .desktop shelf launcher (click = shuffle + skip, then exits)
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
echo "[3/6] writing shuffle wrapper script..."
cat > scripts/ez_jukebox_shuffle.sh <<'WRAP_EOF'
#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - one-shot shuffle+skip; run by the shelf launcher
set -uo pipefail
LOG="${HOME}/.local/share/ez_jukebox/shuffle.log"
mkdir -p "$(dirname "$LOG")"

if ! command -v mpc >/dev/null 2>&1; then
    echo "$(date): [error] mpc not found" >> "$LOG"
    exit 1
fi

if ! mpc status >/dev/null 2>&1; then
    echo "$(date): [warn] MPD not responding -- restarting" >> "$LOG"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi

mpc random on  >> "$LOG" 2>&1
mpc next       >> "$LOG" 2>&1
echo "$(date): shuffled -- now playing: $(mpc current 2>/dev/null)" >> "$LOG"
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
echo "[6/6] git commit..."
git add assets/ez_jukebox_icon.png scripts/ez_jukebox_shuffle.sh scripts/install_shuffle_launcher.sh
git status --short
git commit -m "fix(tray): replace crashing GTK StatusIcon tray with .desktop shelf launcher

Gtk.StatusIcon (pystray's GTK backend) is deprecated since GTK 3.14 and
doesn't implement the systray protocol properly under Wayland/sommelier --
this was the root cause of both the earlier widget assertion crash and
the perpetual 'loading' shelf state. Replaced with a stateless .desktop
launcher: click runs mpc random+next and exits immediately, no persistent
process, no GTK main loop, nothing for the shelf to wait on."

echo ""
echo "=== Done ==="
echo "Find 'ez_jukebox Shuffle' in the ChromeOS app launcher (search or"
echo "all-apps view), then right-click -> Pin to shelf. No more stuck icon."
echo "Log at ~/.local/share/ez_jukebox/shuffle.log for troubleshooting."
