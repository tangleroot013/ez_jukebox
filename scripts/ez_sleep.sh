#!/usr/bin/env bash
# ez_sleep.sh - Fade out volume and pause playback after N minutes
MINUTES=${1:-30}
echo "[ez_jukebox] Sleep timer active: pausing in $MINUTES minute(s)."
sleep $((MINUTES * 60))

START_VOL=$(mpc volume | awk '{print $2}' | tr -d '%')
START_VOL=${START_VOL:-100}

for vol in $(seq "$START_VOL" -5 0); do
    mpc volume "$vol" > /dev/null
    sleep 0.5
done

mpc pause
mpc volume "$START_VOL" > /dev/null
notify-send -a "ez_jukebox" "Sleep Timer" "Playback paused. Goodnight!"
