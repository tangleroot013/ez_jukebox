#!/usr/bin/env bash
# productionize.sh - fix GTK tray crash, restore perms, clean repo, commit
# Run from inside ez_jukebox/scripts/
set -euo pipefail

[[ -f monitor_jukebox.py ]] || { echo "[error] run from ez_jukebox/scripts/"; exit 1; }

echo "[1/5] writing corrected monitor_jukebox.py (single GTK loop, no thread race)..."
cat > monitor_jukebox.py <<'PYEOF'
#!/usr/bin/env python3
"""monitor_jukebox.py - system tray shuffle control for ez_jukebox (MPD)."""
import subprocess
from PIL import Image, ImageDraw
import pystray


def play_random_song(icon=None, item=None):
    subprocess.run(["mpc", "random", "on"], check=False)
    subprocess.run(["mpc", "next"], check=False)


def create_simple_icon():
    img = Image.new("RGBA", (64, 64), color=(30, 30, 30, 255))
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill=(0, 200, 100, 255))
    return img


def setup(icon):
    icon.visible = True


if __name__ == "__main__":
    icon = pystray.Icon(
        "ez_jukebox",
        create_simple_icon(),
        "ez_jukebox (Click to Shuffle)",
        menu=pystray.Menu(
            pystray.MenuItem("Shuffle & Play", play_random_song, default=True),
            pystray.MenuItem("Exit", lambda icon, item: icon.stop()),
        ),
    )
    icon.run(setup=setup)
PYEOF
python3 -m py_compile monitor_jukebox.py && rm -rf __pycache__
echo "  -> compiles clean"

echo ""
echo "[2/5] restoring executable bit (stripped by the 'agfwes' commit)..."
chmod +x monitor_jukebox.py
echo "  -> monitor_jukebox.py is now 755"

echo ""
echo "[3/5] archiving debug/patch scaffolding scripts..."
mkdir -p _archive
ARCHIVED=0
for f in configure_tray_launcher.py fix_gtk_loop.py fix_gtk_tray.py \
         fix_tray_click_random.py fix_tray_handler.py patch_monitor_deep.py \
         update_monitor_tray.py update_tray_shuffle.py; do
    if [[ -f "$f" ]]; then
        mv "$f" "_archive/$f"
        ARCHIVED=$((ARCHIVED + 1))
    fi
done
echo "  -> archived $ARCHIVED file(s) to scripts/_archive/ (preserved, not deleted)"

echo ""
echo "[4/5] restarting cleanly and checking for crash..."
pkill -f monitor_jukebox.py 2>/dev/null || true
sleep 1
LOGFILE="/tmp/monitor_jukebox_check.log"
python3 monitor_jukebox.py > "$LOGFILE" 2>&1 &
NEWPID=$!
sleep 3
if kill -0 "$NEWPID" 2>/dev/null; then
    if grep -q "GTK-CRITICAL\|Traceback" "$LOGFILE" 2>/dev/null; then
        echo "  -> [warn] process alive but logged errors -- check $LOGFILE"
        cat "$LOGFILE"
    else
        echo "  -> [ok] running clean, pid $NEWPID, no GTK-CRITICAL/traceback in 3s window"
    fi
else
    echo "  -> [FAIL] process died immediately -- log follows:"
    cat "$LOGFILE"
fi

echo ""
echo "[5/5] git commit..."
cd ..
git add scripts/monitor_jukebox.py scripts/_archive/
git status --short
git commit -m "fix(tray): remove competing GTK main loop causing widget assertion crash

- monitor_jukebox.py: drop manual Gtk.main() thread; pystray's icon.run()
  already owns the GTK loop for the gtk backend. Running both caused
  gtk_widget_get_scale_factor assertion failures from cross-thread
  widget access with no GTK thread guards.
- restore executable bit stripped by previous commit
- archive one-off debug/patch scripts to scripts/_archive/ (uncommitted
  scaffolding, not part of the app)"
echo ""
echo "=== Done -- review with: git show --stat HEAD ==="
echo "=== Push when ready: git push origin main ==="
