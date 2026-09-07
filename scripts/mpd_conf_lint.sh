#!/usr/bin/env bash
# mpd_conf_lint.sh - reject known-invalid mpd.conf keys before restarting mpd.
# Run standalone, or wire into ez_preflight.sh / systemctl restart wrapper.
set -euo pipefail

MPD_CONF="${1:-${XDG_CONFIG_HOME:-$HOME/.config}/mpd/mpd.conf}"
[[ -f "$MPD_CONF" ]] || { echo "❌ mpd.conf not found: $MPD_CONF"; exit 1; }

# Keys that look plausible but aren't real mpd.conf directives.
# Format: "bad_key:correct_key_or_hint"
declare -A BAD_KEYS=(
    [socket_path]="bind_to_address (for a unix socket, e.g. bind_to_address \"/run/user/1000/mpd/socket\")"
    [db_path]="db_file"
    [pidfile]="pid_file"
    [logfile]="log_file"
    [music_dir]="music_directory"
    [playlist_dir]="playlist_directory"
    [output]="audio_output { ... } block"
)

found=0
for bad in "${!BAD_KEYS[@]}"; do
    if grep -nE "^\s*${bad}\b" "$MPD_CONF" >/dev/null; then
        found=1
        line=$(grep -nE "^\s*${bad}\b" "$MPD_CONF" | head -1)
        echo "❌ invalid key '$bad' at line ${line%%:*}"
        echo "   → use: ${BAD_KEYS[$bad]}"
    fi
done

if [[ "$found" -eq 1 ]]; then
    echo ""
    echo "Refusing to restart mpd with invalid config. Fix line(s) above, then rerun."
    exit 1
fi

echo "✅ $MPD_CONF: no known-invalid keys found"
