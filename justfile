set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

verify:
    python3 scripts/check_integrity.py
    python3 scripts/dedup_triage.py

dedup-triage:
    python3 scripts/dedup_triage.py

check-integrity:
    python3 scripts/check_integrity.py

recover:
    python3 scripts/recover.py

git-sync:
    git add project.json justfile scripts src docs test README.md .gitignore
    git commit -m "Add integrity, dedup triage, and recovery tooling" || true

# --- ez_jukebox Utilities ---

# Start background track notification daemon
notify:
    ./scripts/ez_notify.sh

# Start sleep timer (usage: just sleep 45)
sleep MIN="30":
    ./scripts/ez_sleep.sh {{MIN}}

# Generate a 25-track smart mix (usage: just mix "Jazz")
mix QUERY:
    ./scripts/ez_mix.sh "{{QUERY}}"

# Run system backup
backup:
    ./scripts/ez_backup.sh

# Process and import staged audio from ~/Music/incoming
intake:
    ./scripts/ez_intake.sh

# Export MPD playlists to config/playlists for Git backup
export-playlists:
    ./scripts/ez_playlists.sh export

# Restore Git-backed playlists into MPD
import-playlists:
    ./scripts/ez_playlists.sh import

# Run system and socket environment pre-flight check
preflight:
    ./scripts/ez_preflight.sh

# Run live 'now_playing.json' exporter for widgets/dashboards
now-playing:
    ./scripts/ez_now_playing.sh

# Evaluate duplicate groups and recommend files to keep
dedup-policy:
    python3 scripts/ez_dedup_policy.py

# Audit library metadata tags for missing fields
tag-lint:
    python3 scripts/ez_tag_lint.py

# Restart daemon and confirm now_playing.json updates
notify-test:
    ./scripts/ez_notify_test.sh

# Pull-style API for now_playing.json (localhost only)
now-playing-api:
    ./scripts/ez_now_playing_api.py

# Launch live terminal UI widget for now_playing API
tui:
    ./scripts/ez_now_playing_tui.py

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
