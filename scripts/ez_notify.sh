#!/usr/bin/env bash
# ez_notify.sh - Sends media notifications with controls and silently updates local infobox metadata

OUT_DIR="$HOME/.local/share/ez_jukebox"
INFOBOX_FILE="$OUT_DIR/now_playing.json"
mkdir -p "$OUT_DIR"

update_infobox_and_notify() {
    # Extract current track metadata
    TITLE=$(mpc current -f "%title%")
    ARTIST=$(mpc current -f "%artist%")
    ALBUM=$(mpc current -f "%album%")
    FILE=$(mpc current -f "%file%")

    # Fallbacks if tags are missing
    [ -z "$TITLE" ] && TITLE="${FILE##*/}"
    [ -z "$TITLE" ] && TITLE="Stopped"
    [ -z "$ARTIST" ] && ARTIST="Unknown Artist"
    [ -z "$ALBUM" ] && ALBUM="Unknown Album"

    # Detect player state and shuffle status
    STATUS_LINE=$(mpc status | grep -E '\[(playing|paused)\]')
    STATE=$(echo "$STATUS_LINE" | grep -oP '\[\K[^\]]+' || echo "stopped")
    SHUFFLE_STATE=$(mpc status | grep -o "random: on" >/dev/null && echo "ON" || echo "OFF")

    # 1. Silently update infobox JSON
    cat << JSON > "$INFOBOX_FILE"
{
  "state": "${STATE}",
  "title": "${TITLE}",
  "artist": "${ARTIST}",
  "album": "${ALBUM}",
  "file": "${FILE:-}",
  "shuffle": "${SHUFFLE_STATE}",
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
JSON

    # Skip desktop notification popup if audio is stopped
    if [ "$STATE" = "stopped" ]; then
        return
    fi

    # 2. Trigger desktop notification with control status indicators (fails gracefully if D-Bus is unavailable)
    ICON="media-playback-start"
    [ "$STATE" = "paused" ] && ICON="media-playback-pause"

    notify-send \
        --app-name="ez_jukebox" \
        --icon="$ICON" \
        --urgency=low \
        --replace-id=999 \
        "🎵 Now Playing [${STATE^^}]" \
        "<b>${TITLE}</b>\n${ARTIST} — <i>${ALBUM}</i>\n\n[⏯ Play/Pause]  [⏭ Next]  [🔀 Shuffle: ${SHUFFLE_STATE}]" 2>/dev/null || true
}

echo "[ez_jukebox] Notification & silent infobox daemon active."

# Initial execution
update_infobox_and_notify

# Event listener loop for track/state transitions
mpc idleloop player | while read -r _; do
    update_infobox_and_notify
done
