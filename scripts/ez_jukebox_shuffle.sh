#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - start or advance the shelf player's managed queue
set -euo pipefail

DATA_DIR="${HOME}/.local/share/ez_jukebox"
LOG="${DATA_DIR}/shuffle.log"
STATE="${DATA_DIR}/shuffle-current"
PRELOAD=3
mkdir -p "$DATA_DIR"

log() {
    printf '%s: %s\n' "$(date)" "$*" >> "$LOG"
}

if ! command -v mpc >/dev/null 2>&1; then
    log "[error] mpc not found"
    exit 1
fi

if ! mpc status >/dev/null 2>&1; then
    log "[warn] MPD not responding -- restarting"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi

current="$(mpc current 2>/dev/null || true)"

if [[ -z "$current" || ! -s "$STATE" ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        exit 1
    fi
    mpc clear >/dev/null
    printf '%s\n' "${tracks[@]}" | while IFS= read -r track; do
        [[ -n "$track" ]] && mpc add "$track" >/dev/null
    done
    mpc random off >/dev/null
    mpc repeat off >/dev/null
    mpc play 1 >/dev/null
else
    mpc next >/dev/null
fi

position="$(mpc status | sed -n 's/.*#\([0-9][0-9]*\)\/[0-9][0-9]*.*/\1/p' | head -n 1)"
position="${position:-1}"
while [[ "$(mpc playlist | wc -l)" -lt "$((position + PRELOAD))" ]]; do
    track="$(mpc listall | shuf -n 1)"
    [[ -z "$track" ]] && break
    mpc add "$track" >/dev/null
done

current="$(mpc current 2>/dev/null || true)"
printf '%s' "$current" > "$STATE"
log "now playing: ${current:-none}; upcoming target: $PRELOAD"
