#!/usr/bin/env bash
set -euo pipefail

# activate venv
source .venv/bin/activate

# sanity‑check python
which python
python --version

# start MPD (user service)
systemctl --user start mpd

# give it a second to spin up
sleep 1

# show status
systemctl --user status mpd --no-pager
