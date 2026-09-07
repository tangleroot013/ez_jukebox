#!/usr/bin/env bash
# fix_mpd_crostini.sh – Atomic MPD Crostini Audio Fix
# OPSEC: Designed for Crostini (dev-channel dedede) with PipeWire/ALSA
# Quack! 🦆

set -euo pipefail
shopt -s inherit_errexit

# --- Constants ---
MPD_CONF="${HOME}/.config/mpd/mpd.conf"
GIT_DIR="${HOME}/ez_jukebox"
BACKUP_DIR="${HOME}/.config/mpd/backups"
LOG_FILE="${HOME}/.config/mpd/fix_mpd_crostini.log"

mkdir -p "$BACKUP_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "🦆 Starting MPD Crostini Audio Fix at $(date)"
echo "📁 MPD_CONF: $MPD_CONF"
echo "📁 GIT_DIR:  $GIT_DIR"

# --- 1. Backup current config ---
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/mpd.conf.bak_${TIMESTAMP}"
cp -v "$MPD_CONF" "$BACKUP_FILE"

# --- 2. Clean illegal directives ---
echo "🧹 Removing illegal MPD directives..."
sed -i '/socket_type/d' "$MPD_CONF" || true
sed -i '/^audio_format {$/,/^}$/d' "$MPD_CONF" || true

# --- 3. Validate config is clean ---
if grep -q "socket_type" "$MPD_CONF"; then
    echo "❌ ERROR: socket_type still present!"
    exit 1
fi
if grep -q "audio_format {" "$MPD_CONF"; then
    echo "❌ ERROR: audio_format block still present!"
    exit 1
fi

echo "✅ Config cleaned. First 30 lines:"
head -n 30 "$MPD_CONF"

# --- 4. Restart MPD with validation ---
echo "🔄 Restarting MPD service..."
systemctl --user daemon-reload
systemctl --user restart mpd
sleep 3

# --- 5. Check service status ---
if systemctl --user is-active mpd >/dev/null 2>&1; then
    echo "✅ MPD service is ACTIVE"
else
    echo "❌ MPD service FAILED to start. Logs:"
    journalctl --user -u mpd -n 20 --no-pager
    exit 1
fi

# --- 6. Test mpc connectivity ---
if mpc status >/dev/null 2>&1; then
    echo "✅ mpc can connect to MPD"
    mpc status
else
    echo "❌ mpc cannot connect. Logs:"
    journalctl --user -u mpd -n 20 --no-pager
    exit 1
fi

# --- 7. Set safe volume & update DB ---
echo "🔊 Setting volume to 75%..."
mpc volume 75
echo "🔄 Updating music database..."
mpc update -w &

# --- 8. Git versioning (OPSEC audit trail) ---
if [ -d "$GIT_DIR/.git" ]; then
    echo "📝 Committing config change to git..."
    cd "$GIT_DIR"
    git add "$MPD_CONF"
    git commit -m "fix: remove illegal socket_type & audio_format; restore MPD service"
    git log --oneline -1
else
    echo "⚠️  Git repo not found at $GIT_DIR – skipping commit"
fi

# --- 9. Final health check ---
echo "🎵 Final status:"
mpc status
echo "📊 Disk usage:"
df -h "$HOME"

echo "🦆 MPD Crostini Audio Fix COMPLETE at $(date)"
echo "📄 Log saved to: $LOG_FILE"
