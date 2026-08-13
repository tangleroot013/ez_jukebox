#!/bin/bash
# ez_jukebox Verification Suite Runner

set -e  # Exit on error

echo "🦆 Running ez_jukebox Verification Suite..."

# Run Python verification
python3 test/verify_suite/verify_pipeline.py

# Additional system checks
echo -e "\n🔍 Running system checks..."
test -f music_manifest.json || { echo "❌ music_manifest.json not found"; exit 1; }
test -d /mnt/chromeos/removable/CarterMedia || { echo "❌ Media path not found"; exit 1; }

echo -e "\n✅ All verifications passed!"
