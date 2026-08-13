set shell := ["bash", "-c"]

# Default help overview
@help:
	@echo "🦆 ez_jukebox Control Deck"
	@echo ""
	@echo "Core Commands:"
	@echo "  just play                   - Launch ncmpcpp player"
	@echo "  just audit                  - Run 10% sampling integrity check"
	@echo "  just audit-deep             - Run full SHA-256 deep scan"
	@echo ""
	@echo "Audiophile Survival Stack:"
	@echo "  just decay-scan [PATH]      - Digital Decay Scanner (find corruption)"
	@echo "  just bitrate-audit [PATH]   - Bitrate Auditor (find quality outliers)"
	@echo "  just sample-rate-check [PATH] - Sample Rate Sentinel (detect high-res waste)"
	@echo "  just full-audit [PATH]      - Run all three scanners in sequence"

# Setup dependencies
install:
	sudo apt install -y mpd mpc ncmpcpp pulseaudio-utils
	pip install mutagen python-mpd2 fastapi uvicorn numpy
	chmod +x src/*.py

setup:
	mkdir -p ~/.config/mpd ~/.ncmpcpp
	cp -n config/mpd.conf ~/.config/mpd/mpd.conf
	cp -n config/ncmpcpp/config ~/.ncmpcpp/config
	systemctl --user enable --now mpd || mpd ~/.config/mpd/mpd.conf

play:
	ncmpcpp

# --- Integrity & Audiophile Audits ---

audit:
	python3 src/integrity_check.py --sample 10

audit-deep:
	python3 src/integrity_check.py --deep

decay-scan PATH="":
	python3 src/decay_scanner.py {{ if PATH != "" { PATH } else { "" } }}

bitrate-audit PATH="":
	python3 src/bitrate_auditor.py {{ if PATH != "" { PATH } else { "" } }}

sample-rate-check PATH="":
	python3 src/sample_rate_sentinel.py {{ if PATH != "" { PATH } else { "" } }}

full-audit PATH="":
	@echo "🦆 Running Full Library Audit Suite..."
	python3 src/decay_scanner.py {{ if PATH != "" { PATH } else { "" } }}
	@echo ""
	python3 src/bitrate_auditor.py {{ if PATH != "" { PATH } else { "" } }}
	@echo ""
	python3 src/sample_rate_sentinel.py {{ if PATH != "" { PATH } else { "" } }}

# --- Maintenance & Library Management ---

organize:
	python3 src/organize_music.py

cleanup *ARGS:
	python3 src/cleanup_music_library.py {{ARGS}}

build-library:
	python3 src/build_music_library.py

# Build or refresh content-hash manifest from external drive
build-manifest PATH="":
	python3 src/build_manifest.py {{ if PATH != "" { PATH } else { "" } }}

# Run live monitor
monitor:
	python3 scripts/monitor_jukebox.py

# Run automated pipeline verification suite
verify:
    bash test/verify_suite/run_verification.sh
