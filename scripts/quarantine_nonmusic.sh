#!/usr/bin/env bash
# quarantine_nonmusic.sh - flags/moves likely non-music files (UI sound effects,
# notification sounds) that got swept into the library by `jukebox organize`
# sourcing from the ~/Music -> ChromeOS Downloads symlink.
set -euo pipefail

LIB="${1:-$HOME/Music-library}"
QUARANTINE="$LIB/_quarantine"
MIN_DURATION="${MIN_DURATION:-20}"   # seconds; shorter = almost certainly a UI sound
EXECUTE="${EXECUTE:-0}"

[[ -d "$LIB" ]] || { echo "[error] library not found: $LIB"; exit 1; }

python3 -c "import mutagen" 2>/dev/null || {
  echo "[info] installing mutagen..."
  pip install --break-system-packages --quiet mutagen
}

mkdir -p "$QUARANTINE"

python3 - "$LIB" "$QUARANTINE" "$MIN_DURATION" "$EXECUTE" <<'PYEOF'
import sys, shutil
from pathlib import Path
from mutagen import File as MutagenFile

lib, quarantine, min_dur, execute = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4] == "1"
lib_path = Path(lib)
quarantine_path = Path(quarantine)

flagged = kept = errors = 0

for f in lib_path.rglob("*"):
    if not f.is_file() or quarantine_path in f.parents:
        continue
    if f.suffix.lower() not in {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".opus"}:
        continue
    try:
        audio = MutagenFile(f)
        dur = audio.info.length if audio and audio.info else 0
    except Exception as e:
        print(f"[error] {f}: {e}")
        errors += 1
        continue

    if dur < min_dur:
        rel = f.relative_to(lib_path)
        dest = quarantine_path / rel
        flagged += 1
        if execute:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                print(f"[skip] already quarantined: {rel}")
                continue
            shutil.move(str(f), str(dest))
            print(f"[ok] quarantined ({dur:.1f}s): {rel}")
        else:
            print(f"[dry-run] would quarantine ({dur:.1f}s): {rel}")
    else:
        kept += 1

print(f"\nSummary: flagged={flagged} kept={kept} errors={errors} mode={'EXECUTE' if execute else 'DRY-RUN'}")
if not execute and flagged:
    print(f"Rerun with EXECUTE=1 to actually move files into {quarantine}")
PYEOF
