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

MPD_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/mpd"
LIB="${EZ_JUKEBOX_LIBRARY:-$HOME/Music-library}"
CONF="${MPD_HOME}/mpd.conf"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

mkdir -p "${MPD_HOME}/playlists" "$LIB"

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

# --- back up any existing conf (no-clobber, timestamped) ---
if [[ -f "$CONF" ]]; then
    cp -n "$CONF" "${CONF}.bak.$(date +%F_%H%M%S)"
    echo "[ok] backed up existing mpd.conf"
fi

cat > "$CONF" <<CONF_EOF
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

gapless_mp3_playback "yes"
replaygain "auto"
replaygain_preamp "0"
replaygain_missing_preamp "0"
replaygain_limit "yes"
volume_normalization "no"
audio_buffer_size "8192"
buffer_before_play "10%"

resampler {
    plugin "${RESAMPLER}"${QUALITY_LINE}
}

audio_output {
    type "pulse"
    name "Crostini CRAS Output"
    mixer_type "software"${SERVER_LINE}
}
CONF_EOF

echo "[ok] wrote ${CONF} (resampler=${RESAMPLER})"

systemctl --user daemon-reload

if systemctl --user restart mpd 2>/dev/null; then
    sleep 1
    echo "[ok] mpd restarted"
    mpc status || echo "[warn] mpc status failed -- check: systemctl --user status mpd"
    mpc outputs || true
else
    echo "[warn] no mpd.service unit found for systemctl -- start manually: mpd ${CONF}"
fi
