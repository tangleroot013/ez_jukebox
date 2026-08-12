#!/usr/bin/env bash
# auto_import_downloads.sh – watch ~/Downloads and auto-import new music
set -euo pipefail

INOTIFY_EVENTS="create,move"
INOTIFY_PATH="${HOME}/Downloads"

inotifywait -m -e "$INOTIFY_EVENTS" "$INOTIFY_PATH" | while read -r event file; do
    [[ "$file" =~ \.(mp3|flac|m4a|ogg)$ ]] || continue
    echo "[info] New file detected: $file"
    ./bin/jukebox build --root "$INOTIFY_PATH" --execute
done
