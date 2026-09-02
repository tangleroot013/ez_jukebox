#!/usr/bin/env bash
# mpd_audiophile_setup.sh - bootstrap an MPD config tuned for the best
# achievable fidelity through ChromeOS Crostini's CRAS/PulseAudio bridge.
#
# CAVEAT: CRAS resamples everything to a fixed 48kHz/stereo mix regardless of
# source format -- there is no bit-perfect/exclusive-mode passthrough inside a
# container. This tunes what IS controllable: resampler quality, ReplayGain
# correctness, gapless playback, and buffer stability -- not literal
# bit-perfect output.

set -euo pipefail
umask 077

MPD_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/mpd"
LIB="${EZ_JUKEBOX_LIBRARY:-$HOME/Music-library}"
CONF="${MPD_HOME}/mpd.conf"
PIPEWIRE_CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pipewire/pipewire.conf.d"
PIPEWIRE_CONF="${PIPEWIRE_CONF_DIR}/10-crostini-buffer.conf"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
RESTART_MPD=1
DRY_RUN=0
PIPEWIRE_QUANTUM="${EZ_JUKEBOX_PIPEWIRE_QUANTUM:-4096}"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Write a Crostini-friendly MPD configuration and optionally restart MPD.

Options:
  --library PATH    Music library path (default: ~/Music-library)
    --quantum SAMPLES PipeWire quantum (default: 4096)
  --no-restart      Write configuration without restarting MPD
  --dry-run         Show the target paths without changing files or services
  -h, --help        Show this help
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --library)
            [[ $# -ge 2 ]] || { echo "Error: --library needs a value." >&2; exit 2; }
            LIB="$2"
            shift 2
            ;;
        --quantum)
            [[ $# -ge 2 ]] || { echo "Error: --quantum needs a value." >&2; exit 2; }
            PIPEWIRE_QUANTUM="$2"
            shift 2
            ;;
        --no-restart)
            RESTART_MPD=0
            shift
            ;;
        --dry-run)
            DRY_RUN=1
            shift
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

if ! [[ "$PIPEWIRE_QUANTUM" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: PipeWire quantum must be a positive integer." >&2
    exit 2
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    printf 'MPD config: %s\nPipeWire config: %s\nLibrary: %s\nQuantum: %s\n' "$CONF" "$PIPEWIRE_CONF" "$LIB" "$PIPEWIRE_QUANTUM"
    exit 0
fi

mkdir -p "${MPD_HOME}/playlists" "$LIB"
mkdir -p "$PIPEWIRE_CONF_DIR"
exec 9>"${MPD_HOME}/.ez_jukebox_setup.lock"
flock -n 9 || { echo "[info] another MPD setup is already running"; exit 0; }

# --- detect the pulse/CRAS socket MPD should talk to ---
PULSE_ADDR=""
if [[ -n "${PULSE_SERVER:-}" ]]; then
    PULSE_ADDR="$PULSE_SERVER"
elif [[ -S "${RUNTIME}/pulse/native" ]]; then
    PULSE_ADDR="unix:${RUNTIME}/pulse/native"
else
    echo "[warn] no pulse/CRAS socket detected -- audio_output will omit 'server' and rely on libpulse defaults."
fi

# --- detect soxr resampler support ---
RESAMPLER="internal"
if command -v mpd >/dev/null 2>&1 && mpd --version 2>/dev/null | grep -qi soxr; then
    RESAMPLER="soxr"
else
    echo "[warn] mpd build lacks libsoxr -- falling back to internal resampler. Reinstall/rebuild mpd with soxr support for higher quality resampling."
fi

QUALITY_LINE=""
[[ "$RESAMPLER" == "soxr" ]] && QUALITY_LINE=' quality "very high"'

SERVER_LINE=""
[[ -n "$PULSE_ADDR" ]] && SERVER_LINE=" server \"${PULSE_ADDR}\""

# --- back up any existing config without overwriting an earlier backup ---
if [[ -f "$CONF" ]]; then
    cp -n "$CONF" "${CONF}.bak.$(date +%F_%H%M%S)"
    echo "[ok] backed up existing mpd.conf"
fi

TEMP_CONF="$(mktemp "${CONF}.tmp.XXXXXX")"
trap 'rm -f "$TEMP_CONF"' EXIT
cat > "$TEMP_CONF" <<CONF_EOF
music_directory "${LIB}"
playlist_directory "${MPD_HOME}/playlists"
db_file "${MPD_HOME}/mpd.db"
log_file "${MPD_HOME}/mpd.log"
pid_file "${MPD_HOME}/mpd.pid"
state_file "${MPD_HOME}/mpdstate"
sticker_file "${MPD_HOME}/sticker.sql"
bind_to_address "127.0.0.1"
port "6600"
filesystem_charset "UTF-8"
auto_update "no"

replaygain "auto"
replaygain_preamp "0"
replaygain_missing_preamp "0"
replaygain_limit "yes"
volume_normalization "no"
max_output_buffer_size "16384"

resampler {
    plugin "${RESAMPLER}"${QUALITY_LINE}
}

audio_output {
    type "pulse"
    name "Crostini CRAS Output"
    mixer_type "software"${SERVER_LINE}
}
CONF_EOF
chmod 600 "$TEMP_CONF"
mv -f "$TEMP_CONF" "$CONF"
trap - EXIT

TEMP_PIPEWIRE="$(mktemp "${PIPEWIRE_CONF}.tmp.XXXXXX")"
trap 'rm -f "$TEMP_PIPEWIRE"' EXIT
cat > "$TEMP_PIPEWIRE" <<PIPEWIRE_EOF
# Crostini focus-switch resilience: configured quantum samples.
context.properties = {
    default.clock.min-quantum = ${PIPEWIRE_QUANTUM}
    default.clock.quantum = ${PIPEWIRE_QUANTUM}
}
PIPEWIRE_EOF
chmod 600 "$TEMP_PIPEWIRE"
mv -f "$TEMP_PIPEWIRE" "$PIPEWIRE_CONF"
trap - EXIT

echo "[ok] wrote ${CONF} and ${PIPEWIRE_CONF} (quantum=${PIPEWIRE_QUANTUM}, resampler=${RESAMPLER})"

if [[ "$RESTART_MPD" -eq 0 ]]; then
    echo "[info] MPD was not restarted (--no-restart)"
    exit 0
fi

if ! command -v systemctl >/dev/null 2>&1; then
    echo "[warn] systemctl unavailable -- start MPD manually with this config"
    exit 0
fi

systemctl --user daemon-reload 2>/dev/null || true
for audio_service in pipewire pipewire-pulse wireplumber; do
    if systemctl --user is-active --quiet "$audio_service" 2>/dev/null; then
        systemctl --user restart "$audio_service" 2>/dev/null || \
            echo "[warn] could not restart $audio_service; restart it manually"
    fi
done
if systemctl --user restart mpd 2>/dev/null; then
    sleep 1
    echo "[ok] mpd restarted"
    if command -v mpc >/dev/null 2>&1; then
        mpc status || echo "[warn] mpc status failed -- check: systemctl --user status mpd"
        mpc outputs || true
    else
        echo "[info] mpc unavailable -- verify MPD manually"
    fi
else
    echo "[warn] no mpd.service unit found for systemctl -- start manually: mpd ${CONF}"
fi
