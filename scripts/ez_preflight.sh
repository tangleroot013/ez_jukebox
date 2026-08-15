#!/usr/bin/env bash
# ez_preflight.sh - Validates MPD socket, directory paths, and manifest readiness

echo "=== ez_jukebox Pre-Flight Check ==="
ERRORS=0

# Check MPD connection
if mpc status >/dev/null 2>&1; then
    echo "[ok] MPD daemon is reachable"
else
    echo "[FAIL] MPD daemon is not responding (check 'systemctl --user status mpd')"
    ERRORS=$((ERRORS + 1))
fi

# Check music library directory
if [ -d "$HOME/Music-library" ]; then
    echo "[ok] Primary library directory exists (~/Music-library)"
else
    echo "[FAIL] Primary library directory missing (~/Music-library)"
    ERRORS=$((ERRORS + 1))
fi

# Check manifest file
if [ -f "music_manifest.json" ]; then
    echo "[ok] music_manifest.json present"
else
    echo "[WARN] music_manifest.json missing (run 'python3 scripts/rebuild_manifest.py')"
fi

# Check systemd path unit state
if systemctl --user is-active --quiet ez-jukebox-import.path 2>/dev/null; then
    echo "[ok] ez-jukebox-import.path service active"
else
    echo "[WARN] ez-jukebox-import.path is not active"
fi

echo "-----------------------------------"
if [ "$ERRORS" -eq 0 ]; then
    echo "[SUCCESS] All critical pre-flight checks passed."
    exit 0
else
    echo "[ERROR] $ERRORS critical check(s) failed."
    exit 1
fi
