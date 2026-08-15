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
