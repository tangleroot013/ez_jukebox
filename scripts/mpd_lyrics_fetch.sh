#!/usr/bin/env bash
# mpd_lyrics_fetch.sh – fetch lyrics for the current track
set -euo pipefail

TITLE=$(mpc -f "%title%" current)
ARTIST=$(mpc -f "%artist%" current)

LYRICS_DIR="${HOME}/.mpd/lyrics"
mkdir -p "$LYRICS_DIR"

LYRICS_FILE="${LYRICS_DIR}/${ARTIST} - ${TITLE}.txt"
curl -s "https://api.musixmatch.com/ws/1.1/matcher.lyrics.get?q_track=${TITLE}&q_artist=${ARTIST}&apikey=YOUR_API_KEY" \
     | jq -r '.message.body.lyrics.lyrics_body' > "$LYRICS_FILE" 2>/dev/null || \
echo "[warn] Lyrics fetch failed – check API key or network." > "$LYRICS_FILE"

[[ -s "$LYRICS_FILE" ]] && echo "[ok] Lyrics saved to $LYRICS_FILE" || rm -f "$LYRICS_FILE"
