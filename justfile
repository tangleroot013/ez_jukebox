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
