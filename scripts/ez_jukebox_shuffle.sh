#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - start or advance the shelf player's managed queue
set -euo pipefail

DATA_DIR="${HOME}/.local/share/ez_jukebox"
LOG="${DATA_DIR}/shuffle.log"
PRELOAD_COUNT=3
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

current_pos="$(mpc current -f '%position%' 2>/dev/null || true)"
queue_len="$(mpc playlist 2>/dev/null | wc -l)"

if [[ -z "$current_pos" || "$queue_len" -eq 0 ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD_COUNT + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        exit 1
    fi
    mpc -q clear
    mpc -q random off
    for track in "${tracks[@]}"; do
        [[ -n "$track" ]] && mpc -q add "$track"
    done
    mpc -q play 1
else
    mpc -q next
    current_pos=$((current_pos + 1))
    upcoming=$((queue_len - current_pos))
    needed=$((PRELOAD_COUNT - upcoming))
    for ((index = 0; index < needed; index++)); do
        track="$(mpc listall | shuf -n 1)"
        [[ -n "$track" ]] && mpc -q add "$track"
    done
fi

log "now playing: $(mpc current 2>/dev/null || true); upcoming target: $PRELOAD_COUNT"
