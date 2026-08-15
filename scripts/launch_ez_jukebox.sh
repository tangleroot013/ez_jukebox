#!/usr/bin/env bash

# 1. Send immediate feedback notification
notify-send -a "ez_jukebox" -i "multimedia-audio-player" "ez_jukebox" "Shuffling library..."

# 2. Ensure MPD database is loaded into the queue if empty
if [ "$(mpc playlist | wc -l)" -eq 0 ]; then
    mpc update --wait
    mpc add /
fi

# 3. Shuffle queue and play
mpc shuffle
mpc play

# 4. Fetch and display track info
sleep 0.5
TITLE=$(mpc current -f "%title%")
ARTIST=$(mpc current -f "%artist%")

notify-send -a "ez_jukebox" -i "multimedia-audio-player" \
    "Now Playing" "${TITLE:-Unknown Track}\nby ${ARTIST:-Unknown Artist}"
