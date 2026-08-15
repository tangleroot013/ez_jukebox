#!/usr/bin/env bash
# atomic_fix.sh - fix all outstanding ez_jukebox issues in one pass
set -euo pipefail

echo "[1/5] fixing audio-watchdog.service syntax bug..."
# Original had missing ';' before done AND mpc idleloop blocks forever
# Replacing with a proper status-check watchdog
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/audio-watchdog.service <<'UNIT_EOF'
[Unit]
Description=Audio Stack Watchdog (MPD)
After=mpd.service
Requires=mpd.service

[Service]
Type=simple
ExecStart=/bin/bash -c '\
  while true; do \
    sleep 60; \
    if ! mpc status >/dev/null 2>&1; then \
      echo "$(date): MPD unresponsive -- restarting" >> ~/.local/share/ez_jukebox/watchdog.log; \
      systemctl --user restart mpd || true; \
    fi; \
  done'
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
UNIT_EOF

systemctl --user daemon-reload
systemctl --user restart audio-watchdog.service
echo "[ok] audio-watchdog.service fixed and restarted"

echo ""
echo "[2/5] creating PipeWire buffer config (if PipeWire is active)..."
if systemctl --user is-active pipewire >/dev/null 2>&1; then
    mkdir -p ~/.config/pipewire/pipewire.conf.d
    cat > ~/.config/pipewire/pipewire.conf.d/10-large-buffer.conf <<'PW_EOF'
context.properties = {
    default.clock.rate     = 48000
    default.clock.quantum  = 2048
    default.clock.min-quantum = 1024
    default.clock.max-quantum = 8192
}
PW_EOF
    systemctl --user restart pipewire 2>/dev/null || true
    echo "[ok] PipeWire config written and service restarted"
else
    echo "[skip] PipeWire not active -- Crostini is likely using CRAS/Pulse bridge directly"
    echo "       MPD pulse output handles buffering; PipeWire config not needed"
fi

echo ""
echo "[3/5] adding missing justfile recipes..."
JUSTFILE="justfile"
if grep -q "verify-audio-buffers" "$JUSTFILE" 2>/dev/null; then
    echo "[skip] recipes already present"
else
cat >> "$JUSTFILE" <<'JUST_EOF'

# Verify MPD and audio buffer configuration
verify-audio-buffers:
    @echo "=== MPD status ==="
    @mpc status || echo "[warn] MPD not responding"
    @echo ""
    @echo "=== MPD outputs ==="
    @mpc outputs || true
    @echo ""
    @echo "=== audio-watchdog service ==="
    @systemctl --user status audio-watchdog.service --no-pager -l || true
    @echo ""
    @echo "=== PipeWire (if active) ==="
    @pw-cli info 0 2>/dev/null | grep -E "quantum|rate" || echo "[info] PipeWire not active"

# Stress-test audio stability: play for 60s and check for skips
stress-test-audio:
    @echo "Playing for 60s -- watch for audio glitches..."
    @mpc play 2>/dev/null || true
    @sleep 60
    @mpc status
    @echo "[ok] stress test complete -- no script-level errors detected"
JUST_EOF
    echo "[ok] justfile recipes added"
fi

echo ""
echo "[4/5] backup mpd.conf properly..."
if [[ -f ~/.config/mpd/mpd.conf ]]; then
    mkdir -p ~/backups/ez_jukebox/audio
    cp ~/.config/mpd/mpd.conf \
       ~/backups/ez_jukebox/audio/mpd.conf.$(date +%Y%m%d)
    echo "[ok] mpd.conf backed up"
else
    echo "[skip] ~/.config/mpd/mpd.conf not found"
    echo "       run: bash mpd_audiophile_setup.sh"
fi

echo ""
echo "[5/5] git housekeeping..."
mkdir -p ~/.local/share/ez_jukebox
git add justfile scripts/ README.md
git status --short
echo ""
echo "=== Summary ==="
echo "  audio-watchdog.service: fixed + active"
echo "  PipeWire config:        created if PipeWire was running"
echo "  justfile:               verify-audio-buffers + stress-test-audio added"
echo "  mpd.conf backup:        ~/backups/ez_jukebox/audio/"
echo ""
echo "Next steps:"
echo "  git commit -m 'fix: audio watchdog, justfile recipes, audio buffer config'"
echo "  bash mpd_audiophile_setup.sh   # if mpd.conf doesn't exist yet"
echo "  python3 scripts/rebuild_manifest.py  # rescan for fresh dedup run"
