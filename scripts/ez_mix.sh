#!/usr/bin/env bash
# ez_mix.sh - Quick-mix generator by keyword
QUERY="$1"
if [ -z "$QUERY" ]; then
    echo "Usage: $0 <artist|genre|album|search_term>"
    exit 1
fi

echo "[ez_jukebox] Building mix for '$QUERY'..."
MATCHES=$(mpc searchany "$QUERY")

if [ -z "$MATCHES" ]; then
    echo "[error] No matches found for '$QUERY'."
    exit 1
fi

mpc clear
echo "$MATCHES" | shuf -n 25 | mpc add
mpc play
echo "[ok] Playing 25 random tracks matching '$QUERY'."
