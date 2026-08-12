#!/usr/bin/env bash
# apply_lowlatency.sh – apply low-latency kernel tweaks
set -euo pipefail

echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
echo "10" | sudo tee /proc/sys/vm/swappiness
echo "5" | sudo tee /proc/sys/vm/dirty_ratio
echo "[ok] Low-latency tweaks applied."
