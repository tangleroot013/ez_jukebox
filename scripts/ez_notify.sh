#!/usr/bin/env bash
# ez_notify.sh - Live desktop notifications on track changes
echo "[ez_jukebox] Listening for track changes..."
title=$(mpc current -f "%title%")
artist=$(mpc current -f "%artist%")
[ -n "$title" ] && notify-send -a "ez_jukebox" -i "multimedia-audio-player" "$title" "by ${artist:-Unknown Artist}"

mpc idleloop player | while read -r _; do
    state=$(mpc status | grep -o '\[playing\]')
    if [ -n "$state" ]; then
        title=$(mpc current -f "%title%")
        artist=$(mpc current -f "%artist%")
        album=$(mpc current -f "%album%")
        notify-send -a "ez_jukebox" -i "multimedia-audio-player" \
            "${title:-Unknown Title}" "by ${artist:-Unknown Artist}${album:+\nAlbum: $album}"
    fi
done
