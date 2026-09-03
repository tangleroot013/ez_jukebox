#!/usr/bin/env bash
set -euo pipefail

echo "======================================================================"
echo "  ez_jukebox: Crostini Window-Switch Stutter Remediation Script"
echo "======================================================================"

PIPEWIRE_CONF_DIR="${HOME}/.config/pipewire/pipewire.conf.d"
mkdir -p "${PIPEWIRE_CONF_DIR}"

PW_BUFFER_CONF="${PIPEWIRE_CONF_DIR}/10-crostini-buffer.conf"
echo "--> Writing PipeWire quantum configuration to ${PW_BUFFER_CONF}..."
cat << 'INNEREOF' > "${PW_BUFFER_CONF}"
context.properties = {
    default.clock.min-quantum = 2048
    default.clock.max-quantum = 8192
    default.clock.quantum     = 4096
}
INNEREOF
echo "[OK] PipeWire quantum buffer locked at 4096 samples."

MPD_CONF="${HOME}/.config/mpd/mpd.conf"
MPD_DROPIN="${HOME}/.config/systemd/user/mpd.service.d/50-audiophile.conf"

echo "--> Cleaning up deprecated MPD parameters..."
for cfg in "${MPD_CONF}" "${MPD_DROPIN}"; do
  if [[ -f "${cfg}" ]]; then
    cp "${cfg}" "${cfg}.bak"
    sed -i '/buffer_before_play/d' "${cfg}"
    sed -i '/gapless_mp3_playback/d' "${cfg}"
    echo "[OK] Cleaned deprecated keys from ${cfg} (backup saved as ${cfg}.bak)"
  fi
done

echo "--> Reloading systemd user daemon..."
systemctl --user daemon-reload
echo "[OK] Systemd user units reloaded."

echo "--> Restarting PipeWire and MPD services..."
systemctl --user restart pipewire pipewire-pulse wireplumber mpd

echo ""
echo "======================================================================"
echo "  [SUCCESS] Audio buffer increased to ~85ms!"
echo "  Try switching between Chrome and Crostini windows while playing music."
echo "======================================================================"
