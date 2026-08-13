#!/usr/bin/env bash
# ez_jukebox Verification Suite Runner

set -e

echo "🦆 Running ez_jukebox Verification Suite..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/verify_pipeline.py"

echo -e "\n✅ Verification suite completed!"
