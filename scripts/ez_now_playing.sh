#!/usr/bin/env bash
# ez_now_playing.sh - Writes current track metadata to JSON on change

OUT_DIR="$HOME/.local/share/ez_jukebox"
OUT_FILE="$OUT_DIR/now_playing.json"
mkdir -p "$OUT_DIR"

update_json() {
    TITLE=$(mpc current -f "%title%")
    ARTIST=$(mpc current -f "%artist%")
    ALBUM=$(mpc current -f "%album%")
    FILE=$(mpc current -f "%file%")
    STATE=$(mpc status | grep -oP '\[\K[^\]]+' | head -1)

    cat << JSON > "$OUT_FILE"
{
  "state": "${STATE:-stopped}",
  "title": "${TITLE:-Unknown Title}",
  "artist": "${ARTIST:-Unknown Artist}",
  "album": "${ALBUM:-Unknown Album}",
  "file": "${FILE:-}",
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
JSON
}

echo "[ez_jukebox] Live metadata stream active -> $OUT_FILE"
update_json

mpc idleloop player | while read -r _; do
    update_json
done
