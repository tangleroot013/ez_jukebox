#!/usr/bin/env bash
# ez_backup.sh - Backs up ez_jukebox configs, scripts, and manifests
BACKUP_DIR="$HOME/ez_jukebox_backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE="$BACKUP_DIR/ez_jukebox_backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

tar -czf "$ARCHIVE" \
    -C "$HOME" \
    scripts \
    music_manifest.json \
    .config/systemd/user/ez-jukebox-import.path \
    .config/systemd/user/ez-jukebox-import.service \
    .config/systemd/user/mpd.service.d/override.conf 2>/dev/null

echo "[ok] Backup created successfully: $ARCHIVE"
