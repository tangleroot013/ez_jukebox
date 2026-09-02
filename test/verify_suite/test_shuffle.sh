#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

mkdir -p "$TEMP_DIR/bin" "$TEMP_DIR/home/.config/ez_jukebox"
cat > "$TEMP_DIR/bin/mpc" <<'MOCK_MPC'
#!/usr/bin/env bash
set -euo pipefail
ROOT="${MOCK_ROOT:?}"
QUEUE="$ROOT/queue"
POSITION="$ROOT/position"
STATE="$ROOT/state"
[[ -f "$QUEUE" ]] || : > "$QUEUE"
[[ -f "$POSITION" ]] || printf '0' > "$POSITION"
[[ -f "$STATE" ]] || printf 'stop' > "$STATE"
[[ "${1:-}" == "-q" ]] && shift
command_name="${1:-}"
shift || true
case "$command_name" in
    ping) ;;
    status) printf 'state: %s\n' "$(<"$STATE")" ;;
    current)
        position="$(<"$POSITION")"
        if [[ "${1:-}" == "-f" ]]; then
            [[ "$position" -gt 0 ]] && printf '%s\n' "$position"
        else
            [[ "$position" -gt 0 ]] && sed -n "${position}p" "$QUEUE"
        fi
        ;;
    playlist) cat "$QUEUE" ;;
    listall) printf '%s\n' track-a.mp3 track-b.mp3 track-c.mp3 track-d.mp3 track-e.mp3 ;;
    clear) : > "$QUEUE"; printf '0' > "$POSITION"; printf 'stop' > "$STATE" ;;
    random) ;;
    add) printf '%s\n' "$1" >> "$QUEUE" ;;
    play) printf '%s' "${1:-1}" > "$POSITION"; printf 'play' > "$STATE" ;;
    next)
        position="$(<"$POSITION")"
        printf '%s' "$((position + 1))" > "$POSITION"
        printf 'play' > "$STATE"
        ;;
    *) printf 'unexpected mpc command: %s\n' "$command_name" >&2; exit 1 ;;
esac
MOCK_MPC

cat > "$TEMP_DIR/bin/notify-send" <<'MOCK_NOTIFY'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${MOCK_ROOT:?}/notifications"
MOCK_NOTIFY
chmod +x "$TEMP_DIR/bin/mpc" "$TEMP_DIR/bin/notify-send"
: > "$TEMP_DIR/notifications"
printf 'PRELOAD_COUNT=1\n' > "$TEMP_DIR/home/.config/ez_jukebox/shuffle.conf"

run_launcher() {
    env HOME="$TEMP_DIR/home" \
        XDG_CONFIG_HOME="$TEMP_DIR/home/.config" \
        XDG_DATA_HOME="$TEMP_DIR/home/.local/share" \
        MOCK_ROOT="$TEMP_DIR" \
        MPD_HOST='secret@mpd.example' \
        PRELOAD_COUNT=2 \
        PATH="$TEMP_DIR/bin:$PATH" \
        bash "$ROOT_DIR/scripts/ez_jukebox_shuffle.sh" "$@"
}

run_launcher --preload 3
[[ "$(wc -l < "$TEMP_DIR/queue")" -eq 4 ]]
[[ "$(<"$TEMP_DIR/state")" == play ]]
run_launcher --lookahead 3
[[ "$(wc -l < "$TEMP_DIR/queue")" -eq 5 ]]
! grep -Fq 'secret@mpd.example' "$TEMP_DIR/home/.local/share/ez_jukebox/shuffle.log" "$TEMP_DIR/notifications"
printf '%s\n' 'offline shuffle test passed'
