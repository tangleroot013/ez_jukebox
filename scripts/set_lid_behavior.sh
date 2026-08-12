#!/usr/bin/env bash
# set_lid_behavior.sh – ignore lid switch events
set -euo pipefail

sudo sed -i 's/^HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
sudo sed -i 's/^HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' /etc/systemd/logind.conf
sudo systemctl restart systemd-logind
echo "[ok] Lid switch events ignored."
