#!/usr/bin/env bash
# ez_intake.sh - Staging area intake pipeline for new audio files

INCOMING="$HOME/Music/incoming"
LIBRARY="$HOME/Music-library"

mkdir -p "$INCOMING" "$LIBRARY"

echo "[ez_jukebox] Scanning staging area: $INCOMING"

COUNT=$(find "$INCOMING" -type f \( -iname "*.mp3" -o -iname "*.flac" -o -iname "*.m4a" -o -iname "*.ogg" -o -iname "*.opus" -o -iname "*.wav" \) | wc -l)

if [ "$COUNT" -eq 0 ]; then
    echo "[info] No new audio files found in $INCOMING"
    exit 0
fi

echo "[info] Found $COUNT staged track(s). Processing import..."

# Transfer tracks to main library root and clean up empty staging dirs
rsync -av --remove-source-files "$INCOMING/" "$LIBRARY/"
find "$INCOMING" -type d -empty -delete

# Rebuild manifest and refresh MPD
echo "[info] Rebuilding library manifest and updating MPD database..."
python3 scripts/rebuild_manifest.py
mpc update

echo "[ok] Intake complete! $COUNT track(s) imported and indexed."
