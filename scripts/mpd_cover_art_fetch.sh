#!/usr/bin/env bash
# mpd_cover_art_fetch.sh – download cover art for the current track
set -euo pipefail

COVER_DIR="${HOME}/.mpd/art"
mkdir -p "$COVER_DIR"

TITLE=$(mpc -f "%title%" current)
ARTIST=$(mpc -f "%artist%" current)
ALBUM=$(mpc -f "%album%" current)

URL="https://coverartarchive.org/release-group/?artist=${ARTIST}&release=${ALBUM}"

echo "[info] Searching for cover art for: ${ARTIST} – ${ALBUM}"
curl -s "$URL" | grep -o 'https://[^"]*\.jpg' | head -n 1 | xargs -I{} curl -s -o "${COVER_DIR}/cover.jpg" "{}"

[[ -f "${COVER_DIR}/cover.jpg" ]] && echo "[ok] Cover art saved to ${COVER_DIR}/cover.jpg" || echo "[warn] No cover art found."
