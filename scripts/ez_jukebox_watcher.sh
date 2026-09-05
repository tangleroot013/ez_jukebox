#!/usr/bin/env bash
set -euo pipefail
PRELOAD=3
DATA_DIR="${HOME}/.local/share/ez_jukebox"
LOG="${DATA_DIR}/watcher.log"
mkdir -p "$DATA_DIR"

log() { printf '%s: %s\n' "$(date)" "$*" >> "$LOG"; }

if ! command -v mpc >/dev/null 2>&1; then
    log "[error] mpc not found"
    exit 1
fi

# Block until exactly one MPD player-state event (song change, play, stop),
# then top up the queue and exit. systemd (Restart=always) relaunches us
# immediately -- a durable, self-healing loop with no internal while() and
# no lock file needed, since systemd guarantees only one instance runs.
mpc idle player >/dev/null 2>&1 || true

if ! mpc status >/dev/null 2>&1; then
    log "[warn] MPD not responding -- restarting"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi

playlist_len="$(mpc playlist | wc -l)"

if [[ "$playlist_len" -eq 0 ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        exit 0
    fi
    printf '%s\n' "${tracks[@]}" | while IFS= read -r track; do
        [[ -n "$track" ]] && mpc add "$track" >/dev/null
    done
    mpc random off >/dev/null
    mpc repeat off >/dev/null
    mpc play 1 >/dev/null
    log "[info] playlist was empty -- reseeded with $((PRELOAD + 1)) tracks"
    exit 0
fi

position="$(mpc status | sed -n 's/.*#\([0-9][0-9]*\)\/[0-9][0-9]*.*/\1/p' | head -n 1)"
position="${position:-1}"

added=0
while [[ "$(mpc playlist | wc -l)" -lt "$((position + PRELOAD))" ]]; do
    track="$(mpc listall | shuf -n 1)"
    [[ -z "$track" ]] && break
    mpc add "$track" >/dev/null
    added=$((added + 1))
done

log "now playing: $(mpc current 2>/dev/null || echo none); topped up $added track(s)"
