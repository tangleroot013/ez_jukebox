#!/usr/bin/env bash
# Install ez_jukebox user services for this checkout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$SERVICE_DIR"

for template in "$REPO_ROOT"/config/ez-jukebox-*.service; do
    service_name="$(basename "$template")"
    sed "s|__EZ_JUKEBOX_ROOT__|$REPO_ROOT|g" "$template" > "$SERVICE_DIR/$service_name"
    chmod 600 "$SERVICE_DIR/$service_name"
    printf '[ok] installed %s\n' "$SERVICE_DIR/$service_name"
done

if ! command -v systemctl >/dev/null 2>&1; then
    echo '[warn] systemctl unavailable; services are installed but not enabled'
    exit 0
fi

systemctl --user daemon-reload
for service_name in ez-jukebox-notify.service ez-jukebox-now-playing-api.service; do
    systemctl --user enable --now "$service_name" || \
        printf '[warn] could not start %s; inspect systemctl --user status %s\n' "$service_name" "$service_name"
done
