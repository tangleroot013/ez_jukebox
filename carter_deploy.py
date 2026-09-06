#!/usr/bin/env python3
"""
Idempotent ez_jukebox repository and live-service deployment.

Run from:
~/home-data/github_projects/ez_jukebox

Actions:
- Verifies the Git repository.
- Removes obsolete service files.
- Writes the canonical systemd unit.
- Installs and reloads the live user service.
- Commits and pushes only when the repository changed.
- Prints a reverse audit using tac.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent
SERVICE_NAME = "ez-jukebox-notify.service"


BASH_DEPLOY = r"""#!/usr/bin/env bash
set -Eeuo pipefail

cd "$REPO"

echo "==> Verifying repository"
test -d .git
test -f justfile

echo "==> Creating required directories"
mkdir -p config scripts systemd src bin assets desktop docs test

echo "==> Removing obsolete repository files"
rm -f \
  config/ez-jukebox-queue.service \
  config/ez-jukebox-notify.service \
  config/ez-jukebox-now-playing-api.service \
  scripts/ez_jukebox_queue_watch.sh \
  scripts/mpd_notify.py \
  scripts/install_user_services.sh

echo "==> Verifying notification script"
test -f scripts/ez_notify.sh
chmod 0755 scripts/ez_notify.sh

echo "==> Writing canonical systemd unit"
cat <<'EOF' > systemd/ez-jukebox-notify.service
[Unit]
Description=ez_jukebox Notification and Infobox Daemon
After=mpd.service
Requires=mpd.service

[Service]
Type=simple
ExecStart=/home/tangleroot013/home-data/github_projects/ez_jukebox/scripts/ez_notify.sh
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=default.target
EOF

chmod 0644 systemd/ez-jukebox-notify.service

echo "==> Installing the live user service"
command -v just >/dev/null 2>&1
just install-service

echo "==> Reloading user systemd"
if command -v systemctl >/dev/null 2>&1; then
    systemctl --user daemon-reload

    if systemctl --user is-enabled --quiet ez-jukebox-notify.service 2>/dev/null; then
        systemctl --user enable ez-jukebox-notify.service >/dev/null
    fi

    if systemctl --user is-active --quiet ez-jukebox-notify.service 2>/dev/null; then
        systemctl --user restart ez-jukebox-notify.service
    else
        systemctl --user start ez-jukebox-notify.service
    fi

    systemctl --user --no-pager --full status \
        ez-jukebox-notify.service || true
else
    echo "systemctl was not found; service files were installed but not started."
fi

echo "==> Updating Git"
git add -A

if git diff --cached --quiet; then
    echo "No repository changes; no commit or push required."
else
    git commit -m "refactor(services): enforce canonical notification service"
    git push origin main
fi

echo "==> Repository status"
git status --short --branch

echo "==> Reverse audit"
if command -v tac >/dev/null 2>&1; then
    find . \
        -path './.git' -prune -o \
        -type f -print | sort | tac
else
    echo "tac is not installed; skipping reverse audit."
fi

echo "==> Deployment complete"
"""


def run() -> int:
    if not (REPO / ".git").is_dir():
        print(f"Not a Git repository: {REPO}", file=sys.stderr)
        return 2

    # The generated Bash script receives REPO through its environment.
    env = os.environ.copy()
    env["REPO"] = str(REPO)

    try:
        subprocess.run(
            ["bash", "-s"],
            input=BASH_DEPLOY,
            text=True,
            cwd=REPO,
            env=env,
            check=True,
        )
    except KeyboardInterrupt:
        print("\nDeployment interrupted with Ctrl-C.", file=sys.stderr)
        return 130
    except subprocess.CalledProcessError as error:
        print(
            f"Deployment failed with exit code {error.returncode}.",
            file=sys.stderr,
        )
        return error.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(run())
