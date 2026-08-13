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
