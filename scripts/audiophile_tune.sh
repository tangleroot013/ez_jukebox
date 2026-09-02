#!/usr/bin/env bash
# audiophile_tune.sh - Crostini skip elimination via layered buffer tuning
# MPD → PulseAudio → CRAS chain; each layer absorbs VM scheduling jitter
set -euo pipefail
umask 077

MPD_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/mpd"
MPD_CONF="${MPD_HOME}/mpd.conf"
PULSE_CONF="${HOME}/.config/pulse/daemon.conf"
PIPEWIRE_CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pipewire/pipewire.conf.d"
PIPEWIRE_CONF="${PIPEWIRE_CONF_DIR}/10-crostini-buffer.conf"
LIB="${EZ_JUKEBOX_LIBRARY:-$HOME/Music-library}"
RUNTIME="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
PIPEWIRE_QUANTUM="${EZ_JUKEBOX_PIPEWIRE_QUANTUM:-4096}"

if ! [[ "$PIPEWIRE_QUANTUM" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: EZ_JUKEBOX_PIPEWIRE_QUANTUM must be a positive integer." >&2
    exit 2
fi

mkdir -p "$(dirname "$MPD_CONF")" "$MPD_HOME/playlists"
mkdir -p "$PIPEWIRE_CONF_DIR"

# detect pulse socket
SERVER_LINE=""
[[ -S "${RUNTIME}/pulse/native" ]] && \
    SERVER_LINE="    server          \"unix:${RUNTIME}/pulse/native\""

echo "[1/5] writing optimised mpd.conf..."
cat > "$MPD_CONF" <<CONF
music_directory     "${LIB}"
playlist_directory  "${MPD_HOME}/playlists"
db_file             "${MPD_HOME}/mpd.db"
log_file            "${MPD_HOME}/mpd.log"
pid_file            "${MPD_HOME}/mpd.pid"
state_file          "${MPD_HOME}/mpdstate"
sticker_file        "${MPD_HOME}/sticker.sql"

bind_to_address     "127.0.0.1"
port                "6600"
filesystem_charset  "UTF-8"
auto_update         "no"

# ── Crostini buffer tuning ──────────────────────────────────────────────────
# max_output_buffer_size is supported by modern MPD builds.
max_output_buffer_size     "16384"

replaygain                "auto"
replaygain_preamp         "0"
replaygain_missing_preamp "0"
replaygain_limit          "yes"
volume_normalization      "no"

resampler {
    plugin "internal"
}

audio_output {
    type            "pulse"
    name            "Crostini CRAS"
    mixer_type      "software"
    buffer_time     "600000"   # 600 ms PulseAudio sink buffer (µs)
    fragment_size   "32768"    # 32 KB fragments → fewer underrun opportunities
${SERVER_LINE}
}
CONF
echo "[ok] mpd.conf: 16MB output buffer, 600ms sink buffer, 32KB fragments"

echo ""
echo "[2/5] writing PipeWire quantum drop-in..."
cat > "$PIPEWIRE_CONF" <<PIPEWIRE
# Crostini focus-switch resilience: configured quantum samples.
context.properties = {
    default.clock.min-quantum = ${PIPEWIRE_QUANTUM}
    default.clock.quantum = ${PIPEWIRE_QUANTUM}
}
PIPEWIRE
chmod 600 "$PIPEWIRE_CONF"
echo "[ok] PipeWire quantum: ${PIPEWIRE_QUANTUM} samples"

echo ""
echo "[3/5] tuning PulseAudio daemon..."
mkdir -p "$(dirname "$PULSE_CONF")"
cat > "$PULSE_CONF" <<PULSE
# Crostini audio stability -- larger fragments absorb VM preemption spikes
default-sample-rate          = 48000
default-sample-format        = s16le
default-fragments            = 8
default-fragment-size-msec   = 75

realtime-scheduling          = no

avoid-resampling             = no
resample-method              = speex-float-3

exit-idle-time               = -1
PULSE
echo "[ok] pulse daemon.conf: 8 x 75ms = 600ms fragment buffer"

echo ""
echo "[4/5] applying..."
systemctl --user daemon-reload

# Restart PulseAudio to pick up daemon.conf
if systemctl --user is-active pulseaudio >/dev/null 2>&1; then
    systemctl --user restart pulseaudio && sleep 1 && echo "[ok] pulseaudio restarted"
elif command -v pulseaudio >/dev/null 2>&1; then
    pulseaudio --kill 2>/dev/null; sleep 1
    pulseaudio --start 2>/dev/null && echo "[ok] pulseaudio restarted"
else
    echo "[skip] pulseaudio not found -- changes apply on next login"
fi

systemctl --user restart mpd && sleep 1

echo ""
echo "[5/5] === Verification ==="
systemctl --user is-active mpd && echo "[ok] MPD active" || echo "[FAIL] MPD not running"
mpc status 2>/dev/null | head -3 || echo "[warn] mpc: no response"
mpc outputs 2>/dev/null | head -5 || true

echo ""
cat <<SUMMARY
=== Buffer chain (Crostini) ===
    MPD output buffer:   16 MB
    PulseAudio sink:     600 ms  (buffer_time)
    PA fragments:        8 × 75 ms = 600 ms
    PipeWire quantum:    ${PIPEWIRE_QUANTUM} samples
    RTKit/realtime:      disabled; relies on buffering instead

=== If skips persist ===
  1. tail -f ~/.mpd/mpd.log   # look for "buffer underrun"
  2. just stress-test-audio   # check for correlation with CPU spikes
  3. Increase buffer_time to 800000 and default-fragment-size-msec to 100
SUMMARY
