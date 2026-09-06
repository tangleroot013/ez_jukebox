#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT

mkdir -p "$TEMP_DIR/data/ez_jukebox" "$TEMP_DIR/library"
printf '%s\n' healthy > "$TEMP_DIR/library/healthy.mp3"
expected_hash="$(sha256sum "$TEMP_DIR/library/healthy.mp3" | awk '{print $1}')"

python3 - "$TEMP_DIR/data/ez_jukebox/music_manifest.json" "$TEMP_DIR/library/healthy.mp3" "$expected_hash" <<'PY'
import json
import sys

manifest_path, healthy_path, healthy_hash = sys.argv[1:]
with open(manifest_path, "w", encoding="utf-8") as manifest_file:
    json.dump(
        {
            "files": {
                healthy_path: healthy_hash,
                "/missing/track.mp3": healthy_hash,
                "/invalid/hash.mp3": "not-a-sha256",
            }
        },
        manifest_file,
    )
PY

set +e
XDG_DATA_HOME="$TEMP_DIR/data" python3 "$ROOT_DIR/scripts/check_integrity.py" > "$TEMP_DIR/output" 2>&1
status=$?
set -e
[[ "$status" -eq 1 ]]
grep -q 'Integrity check failed:' "$TEMP_DIR/output"
grep -q 'missing' "$TEMP_DIR/output"
grep -q 'invalid_manifest_hash' "$TEMP_DIR/output"
report_count="$(python3 - "$TEMP_DIR/data/ez_jukebox/reports/integrity_report.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as report_file:
    print(len(json.load(report_file)["results"]))
PY
)"
[[ "$report_count" -eq 3 ]]
printf '%s\n' 'offline integrity test passed'
