#!/usr/bin/env bash
# mpd_now_playing_json.sh – output current track as JSON
set -euo pipefail

TITLE=$(mpc -f "%title%" current)
ARTIST=$(mpc -f "%artist%" current)
ALBUM=$(mpc -f "%album%" current)
POSITION=$(mpc -f "%position%" current)
DURATION=$(mpc -f "%time%" current)

jq -n \
   --arg title "$TITLE" \
   --arg artist "$ARTIST" \
   --arg album "$ALBUM" \
   --argjson pos "$POSITION" \
   --arg duration "$DURATION" \
   '{title: $title, artist: $artist, album: $album, position: $pos, duration: $duration}'
