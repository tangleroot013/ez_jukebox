#!/bin/bash
set -euo pipefail

echo "Cleaning the pond..."
rm -rf .venv

echo "Creating isolated venv..."
python3 -m venv .venv

echo "Installing verified dependencies..."
# thefuzz is the core, python-Levenshtein makes it fast
.venv/bin/pip install --upgrade pip
.venv/bin/pip install thefuzz python-Levenshtein

echo "Venv established and verified. Quack!"
