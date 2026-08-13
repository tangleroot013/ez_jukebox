#!/usr/bin/env python3
"""find_orphans_manifest.py - flags music_manifest.json entries whose files
no longer exist on disk. Read-only; reports only, moves/deletes nothing."""
import json, re, sys
from pathlib import Path

HASH_RE = re.compile(r"^[0-9a-f]{32,64}$", re.IGNORECASE)


def looks_like_hash(s):
    return isinstance(s, str) and bool(HASH_RE.match(s))


manifest_path = Path(sys.argv[1] if len(sys.argv) > 1 else "music_manifest.json")
if not manifest_path.exists():
    print(f"[error] manifest not found: {manifest_path}")
    sys.exit(1)

data = json.loads(manifest_path.read_text())
if not isinstance(data, dict) or not data:
    print(f"[error] unexpected manifest shape: {type(data)}")
    sys.exit(1)

sample_key = next(iter(data.keys()))
sample_val = next(iter(data.values()))

if isinstance(sample_val, str):
    if looks_like_hash(sample_val) and not looks_like_hash(sample_key):
        paths = list(data.keys())
    elif looks_like_hash(sample_key) and not looks_like_hash(sample_val):
        paths = list(data.values())
    else:
        print(f"[error] ambiguous orientation -- sample key={sample_key!r} val={sample_val!r}")
        sys.exit(1)
elif isinstance(sample_val, list):
    paths = [p for entries in data.values() for p in entries]
else:
    print(f"[error] unrecognized manifest shape (values are {type(sample_val)})")
    sys.exit(1)

print(f"Scanning {len(paths)} manifest entries for missing files...")

orphans = [p for p in paths if not Path(p).exists()]

if not orphans:
    print("[ok] library is fully synced -- no missing files detected")
else:
    for p in orphans:
        print(f"  [!] missing: {p}")
    print(f"\n[warn] found {len(orphans)} orphaned manifest entries")
    print("  tip: rerun the manifest build to clear these out")
