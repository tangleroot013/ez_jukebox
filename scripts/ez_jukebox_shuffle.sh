#!/usr/bin/env bash
# ez_jukebox_shuffle.sh - start or advance the shelf player's managed queue
set -euo pipefail
umask 077

CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/ez_jukebox/shuffle.conf"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/ez_jukebox"
LOG="${DATA_DIR}/shuffle.log"
environment_preload="${PRELOAD_COUNT:-}"
environment_host="${MPD_HOST:-}"
environment_port="${MPD_PORT:-}"
PRELOAD_COUNT=3
MPD_HOST=localhost
MPD_PORT=6600

if [[ -f "$CONFIG_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$CONFIG_FILE"
fi
PRELOAD_COUNT="${environment_preload:-${PRELOAD_COUNT}}"
MPD_HOST="${environment_host:-${MPD_HOST}}"
MPD_PORT="${environment_port:-${MPD_PORT}}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [options]

Start background shuffle playback or advance to the next track.

Options:
  --host HOST       MPD host (default: configured MPD_HOST or localhost)
  --port PORT       MPD port (default: configured MPD_PORT or 6600)
    --preload COUNT   Upcoming tracks to maintain (default: 3)
    --lookahead COUNT Alias for --preload
  -h, --help        Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            [[ $# -ge 2 ]] || { echo "Error: --host needs a value." >&2; exit 2; }
            MPD_HOST="$2"
            shift 2
            ;;
        --port)
            [[ $# -ge 2 ]] || { echo "Error: --port needs a value." >&2; exit 2; }
            MPD_PORT="$2"
            shift 2
            ;;
        --preload|--lookahead)
            [[ $# -ge 2 ]] || { echo "Error: --preload needs a value." >&2; exit 2; }
            PRELOAD_COUNT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown option '$1'. Use --help for usage." >&2
            exit 2
            ;;
    esac
done

if ! [[ "$PRELOAD_COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: preload count must be a positive integer." >&2
    exit 2
fi
if ! [[ "$MPD_PORT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: MPD port must be a positive integer." >&2
    exit 2
fi

export MPD_HOST MPD_PORT
mkdir -p "$DATA_DIR"
exec 9>"$DATA_DIR/shuffle.lock"
flock -n 9 || exit 0

log() {
    printf '%s: %s\n' "$(date)" "$*" >> "$LOG"
}

notify() {
    notify-send "$1" "$2" >/dev/null 2>&1 || true
}

for command_name in mpc; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        message="Error: '$command_name' is required but not installed."
        log "[error] $message"
        printf '%s\n' "$message" >&2
        exit 1
    fi
done

safe_host="${MPD_HOST##*@}"
if ! mpc status >/dev/null 2>&1; then
    log "[warn] MPD connection failed for ${safe_host}:${MPD_PORT}; restarting user service"
    systemctl --user restart mpd 2>/dev/null || true
    sleep 1
fi
if ! mpc status >/dev/null 2>&1; then
    message="MPD is unavailable at ${safe_host}:${MPD_PORT}."
    log "[error] $message"
    notify "ez_jukebox" "$message"
    exit 1
fi

current_pos="$(mpc current -f '%position%' 2>/dev/null || true)"
queue_len="$(mpc playlist 2>/dev/null | wc -l)"
state="$(mpc status 2>/dev/null | sed -n 's/^state: //p')"

if [[ -z "$current_pos" || "$queue_len" -eq 0 || "$state" == "stop" ]]; then
    mapfile -t tracks < <(mpc listall | shuf -n "$((PRELOAD_COUNT + 1))")
    if [[ "${#tracks[@]}" -eq 0 ]]; then
        log "[error] MPD library is empty"
        notify "ez_jukebox" "No tracks found in the MPD library."
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
        track="$(mpc listall | grep -Fvx -f <(mpc playlist) | shuf -n 1 || true)"
        [[ -n "$track" ]] && mpc -q add "$track"
    done
fi

current="$(mpc current 2>/dev/null || true)"
log "now playing: ${current:-none}; upcoming target: $PRELOAD_COUNT"
notify "ez_jukebox" "${current:-Playback started}"
