#!/usr/bin/env bash
# mpd_clean_start.sh – guarantee a single, clean MPD instance
# Quack!  –  duck‑style safe‑startup for Crostini

set -euo pipefail   # abort on error, unset vars, or pipeline failure

MPD_CONF="${HOME}/.config/mpd/mpd.conf"
MPD_DIR="${HOME}/.config/mpd"
MPD_PID="${MPD_DIR}/mpd.pid"
MPD_DB="${MPD_DIR}/mpd.db"
MPD_PORT=6600

# -------------------------------------------------------------------------
# 1️⃣ Stop the managed service (if it’s running) and kill any stray MPD proc
# -------------------------------------------------------------------------
echo "⏹️  Stopping user MPD service (if active)…"
systemctl --user stop mpd || true

echo "🔪  Killing stray MPD processes…"
pkill -9 mpd || true

# -------------------------------------------------------------------------
# 2️⃣ Remove stale pid / db files (they can block startup)
# -------------------------------------------------------------------------
for stale in "${MPD_PID}" "${MPD_DB}"; do
    if [[ -e "${stale}" ]]; then
        echo "🗑️  Removing stale file: ${stale}"
        rm -f "${stale}"
    fi
done

# -------------------------------------------------------------------------
# 3️⃣ Ensure port ${MPD_PORT} is truly free
# -------------------------------------------------------------------------
if ss -ltnp | grep -q ":${MPD_PORT}"; then
    echo "⚠️  Port ${MPD_PORT} is still bound – hunting the offender…"
    # Grab the PID(s) listening on the port and kill them
    offenders=$(ss -ltnp | awk "/:${MPD_PORT}/ {print \$6}" | cut -d',' -f2)
    for pid in ${offenders}; do
        echo "🔨  Killing PID ${pid} occupying ${MPD_PORT}"
        kill -9 "${pid}"
    done
else
    echo "✅  Port ${MPD_PORT} is free."
fi

# -------------------------------------------------------------------------
# 4️⃣ Reload systemd daemon and (re)start the user service
# -------------------------------------------------------------------------
echo "🔄  Reloading user systemd daemon…"
systemctl --user daemon-reload

echo "🚀  Starting MPD service…"
systemctl --user start mpd

# -------------------------------------------------------------------------
# 5️⃣ Give it a moment, then report status
# -------------------------------------------------------------------------
sleep 1

echo "📡  MPD socket check:"
ss -ltnp | grep ":${MPD_PORT}" || echo "❌  No listener on ${MPD_PORT}"

echo "🔎  MPD service status:"
systemctl --user --no-pager --full status mpd.service

echo "🎧  mpc status:"
mpc status || echo "❌  mpc cannot connect (still a problem?)"

echo "✅  Clean start complete. Quack! 🦆"
