#!/usr/bin/env python3
"""
dedup_executor.py - dry-run-by-default dedup executor driven by music_manifest.json

For each hash group with >1 file, picks one "keeper" and moves the rest
(never deletes) into LIBRARY_ROOT/_dedup_quarantine/, mirroring relative path.
Fully reversible / idempotent.

Keeper selection (first rule producing a unique winner wins):
  1. Not already inside a quarantine folder
  2. Path lives under LIBRARY_ROOT (canonical) over external/staging paths
  3. Richer tags (artist+album+title present) -- skip with --no-tag-check
  4. Shortest path
  5. Alphabetically first

Usage:
  python3 dedup_executor.py music_manifest.json                 # dry run
  EXECUTE=1 python3 dedup_executor.py music_manifest.json        # actually move
  python3 dedup_executor.py music_manifest.json --no-tag-check   # skip mutagen pass
  python3 dedup_executor.py music_manifest.json --limit=50       # preview on subset
  python3 dedup_executor.py music_manifest.json --debug-shape    # inspect manifest structure only
"""
import json, os, re, sys, shutil, time
from pathlib import Path
from collections import defaultdict

HASH_RE = re.compile(r"^[0-9a-f]{32,64}$", re.IGNORECASE)


def looks_like_hash(s):
    return isinstance(s, str) and bool(HASH_RE.match(s))

LIBRARY_ROOT = Path(os.environ.get("LIBRARY_ROOT", str(Path.home() / "Music-library"))).resolve()
QUARANTINE = LIBRARY_ROOT / "_dedup_quarantine"
EXECUTE = os.environ.get("EXECUTE", "0") == "1"
NO_TAG_CHECK = "--no-tag-check" in sys.argv
DEBUG_SHAPE = "--debug-shape" in sys.argv
LIMIT = None
for a in sys.argv[1:]:
    if a.startswith("--limit="):
        LIMIT = int(a.split("=", 1)[1])
manifest_arg = next((a for a in sys.argv[1:] if not a.startswith("--")), "music_manifest.json")
MANIFEST = Path(manifest_arg)


def read_manifest(path):
    if not path.exists():
        print(f"[error] manifest not found: {path}")
        sys.exit(1)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"[error] {path} is not valid JSON: {e}")
        sys.exit(1)


def debug_shape(data):
    print(f"[debug] top-level type: {type(data).__name__}")
    if isinstance(data, dict):
        print(f"[debug] top-level key count: {len(data)}")
        for k in list(data.keys())[:8]:
            v = data[k]
            print(f"[debug]   key={k!r} type={type(v).__name__} preview={repr(v)[:100]}")
    elif isinstance(data, list):
        print(f"[debug] top-level list length: {len(data)}")
        for item in data[:3]:
            print(f"[debug]   item preview={repr(item)[:120]}")
    else:
        print(f"[debug] unexpected top-level type: {type(data)}")


def load_groups(data):
    groups = defaultdict(list)

    # v2.1 wrapped shape: {"metadata": {...}, "files": {path: hash, ...}}
    if isinstance(data, dict) and isinstance(data.get("files"), dict):
        for p, h in data["files"].items():
            if p and h:
                groups[h].append(p)
        print(f"[info] detected wrapped manifest shape (metadata + files) -- {len(data['files']):,} files indexed")
        return groups

    if isinstance(data, dict):
        sample_val = next(iter(data.values()), None)
        if isinstance(sample_val, list):
            for h, entries in data.items():
                for e in entries:
                    p = e.get("path") if isinstance(e, dict) else e
                    if p:
                        groups[h].append(p)
        elif isinstance(sample_val, str):
            sample_key = next(iter(data.keys()))
            key_is_hash = looks_like_hash(sample_key)
            val_is_hash = looks_like_hash(sample_val)
            if val_is_hash and not key_is_hash:
                for p, h in data.items():
                    if p and h:
                        groups[h].append(p)
            elif key_is_hash and not val_is_hash:
                for h, p in data.items():
                    if p and h:
                        groups[h].append(p)
            else:
                print(f"[error] ambiguous orientation -- sample key={sample_key!r} val={sample_val!r}")
                print("Neither side matches a hash pattern cleanly. Rerun with --debug-shape to inspect.")
                sys.exit(1)
        elif isinstance(sample_val, dict):
            for p, meta in data.items():
                h = meta.get("hash") or meta.get("sha256") or meta.get("content_hash")
                if p and h:
                    groups[h].append(p)
        else:
            print(f"[error] unrecognized manifest shape (dict values are {type(sample_val)})")
            print("Rerun with --debug-shape to inspect the manifest structure.")
            sys.exit(1)
    elif isinstance(data, list):
        for e in data:
            if not isinstance(e, dict):
                continue
            h = e.get("hash") or e.get("sha256") or e.get("content_hash")
            p = e.get("path") or e.get("file") or e.get("filepath")
            if h and p:
                groups[h].append(p)
    else:
        print(f"[error] unexpected top-level type: {type(data)}")
        sys.exit(1)
    return groups


def is_quarantined(p: str) -> bool:
    parts = Path(p).parts
    return "_quarantine" in parts or "_dedup_quarantine" in parts


def is_canonical(p: str) -> bool:
    try:
        rp = Path(p).resolve()
        return LIBRARY_ROOT in rp.parents
    except Exception:
        return False


def tag_richness(p: str) -> int:
    if NO_TAG_CHECK:
        return 0
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(p, easy=True)
        if not audio or not audio.tags:
            return 0
        score = 0
        for key in ("artist", "album", "title"):
            val = audio.tags.get(key)
            if val and str(val[0]).strip():
                score += 1
        return score
    except Exception:
        return 0


def pick_keeper(paths):
    candidates = [p for p in paths if Path(p).exists()]
    if not candidates:
        return None, paths
    pool = [p for p in candidates if not is_quarantined(p)] or candidates
    canon = [p for p in pool if is_canonical(p)]
    pool = canon or pool
    if len(pool) > 1:
        scored = [(tag_richness(p), p) for p in pool]
        best = max(s for s, _ in scored)
        pool = [p for s, p in scored if s == best]
    if len(pool) > 1:
        min_len = min(len(p) for p in pool)
        pool = [p for p in pool if len(p) == min_len]
    keeper = sorted(pool)[0]
    dupes = [p for p in candidates if p != keeper]
    return keeper, dupes


def main():
    data = read_manifest(MANIFEST)

    if DEBUG_SHAPE:
        debug_shape(data)
        return

    groups = load_groups(data)
    total_indexed = sum(len(v) for v in groups.values())
    if total_indexed == 0:
        print("[warn] 0 entries indexed from manifest -- shape may not be recognized.")
        print("       Rerun with --debug-shape to inspect the manifest structure before assuming there are no duplicates.")

    dupe_groups = {h: paths for h, paths in groups.items() if len(paths) > 1}
    items = list(dupe_groups.items())
    if LIMIT:
        items = items[:LIMIT]

    print(f"[info] {len(items)}/{len(dupe_groups)} hash groups queued -- mode={'EXECUTE' if EXECUTE else 'DRY-RUN'}")
    if not NO_TAG_CHECK:
        print("[info] tag-richness check enabled (slower); pass --no-tag-check to skip")

    planned = skipped = missing = errors = 0
    reclaimed_bytes = 0
    start = time.time()

    for i, (h, paths) in enumerate(items, 1):
        keeper, dupes = pick_keeper(paths)
        if keeper is None:
            print(f"[skip] {h[:12]}... no surviving files on disk")
            skipped += 1
            continue
        for d in dupes:
            src = Path(d)
            if not src.exists():
                missing += 1
                continue
            try:
                rel = src.resolve().relative_to(LIBRARY_ROOT) if is_canonical(str(src)) else Path(src.name)
            except Exception:
                rel = Path(src.name)
            dest = QUARANTINE / rel
            if EXECUTE:
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists():
                        print(f"[skip] already quarantined: {src}")
                        skipped += 1
                        continue
                    size = src.stat().st_size
                    shutil.move(str(src), str(dest))
                    reclaimed_bytes += size
                    planned += 1
                except Exception as e:
                    print(f"[error] {src}: {e}")
                    errors += 1
            else:
                try:
                    reclaimed_bytes += src.stat().st_size
                except Exception:
                    pass
                planned += 1
        if i % 500 == 0:
            print(f"[info] processed {i}/{len(items)} groups...")

    elapsed = time.time() - start
    mb = reclaimed_bytes / (1024 * 1024)
    action = "quarantined" if EXECUTE else "planned"
    print(f"\nSummary: {action}={planned} skipped={skipped} missing={missing} errors={errors} "
          f"reclaimed≈{mb:.1f}MB elapsed={elapsed:.1f}s mode={'EXECUTE' if EXECUTE else 'DRY-RUN'}")
    if not EXECUTE and planned:
        print(f"Rerun with EXECUTE=1 to actually move {planned} duplicate files into {QUARANTINE}")


if __name__ == "__main__":
    main()
