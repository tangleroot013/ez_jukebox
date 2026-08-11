#!/usr/bin/env python3
"""
cleanup_music_library.py - Run AFTER build_music_library.py.
Removes stray/junk files, deletes broken/unreadable audio, dedupes anything
that slipped through inside the Music tree itself, fills in missing tags
by inferring from folder structure + filename, prunes empty dirs, and
reconciles the manifest against what's actually on disk.
Report-only by default; pass --execute to actually change anything.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".aiff", ".opus"}
KEEP_EXTS = {".jpg", ".jpeg", ".png", ".webp"}  # cover art, never touched
STRAY_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
STRAY_EXTS = {".part", ".crdownload", ".tmp", ".download", ".url", ".ini", ".nfo", ".bak", ".torrent"}
TRACK_PREFIX_RE = re.compile(r"^\s*(\d{1,3})[\s\-\._]+(.*)$")


def sha256_of(path: Path, chunk_size=1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def is_broken_audio(path: Path) -> bool:
    try:
        if path.stat().st_size == 0:
            return True
    except OSError:
        return True
    if not HAS_MUTAGEN:
        return False  # can't verify without mutagen; don't false-flag
    try:
        audio = MutagenFile(path)
        return audio is None
    except Exception:
        return True


def parse_title_from_filename(stem: str):
    """Return (track_num_or_None, cleaned_title)."""
    m = TRACK_PREFIX_RE.match(stem)
    if m:
        return m.group(1).zfill(2), m.group(2).strip()
    return None, stem.strip()


def fix_tags(path: Path, artist_hint: str, album_hint: str, execute: bool) -> bool:
    """Fill missing artist/album/title/track from folder+filename. Returns True if changed (or would change)."""
    if not HAS_MUTAGEN:
        return False
    try:
        audio = MutagenFile(path, easy=True)
    except Exception as e:
        print(f"  WARN could not open for tagging {path}: {e}")
        return False
    if audio is None:
        return False

    if audio.tags is None:
        try:
            audio.add_tags()
        except Exception:
            return False  # format doesn't support tags (e.g. plain WAV without ID3 support)

    cur_artist = (audio.get("artist") or [None])[0]
    cur_album = (audio.get("album") or [None])[0]
    cur_title = (audio.get("title") or [None])[0]
    cur_track = (audio.get("tracknumber") or [None])[0]

    fname_track, fname_title = parse_title_from_filename(path.stem)
    changed = False
    new_vals = {}

    if not cur_artist or cur_artist.strip().lower() == "unknown artist":
        new_vals["artist"] = artist_hint
        changed = True
    if not cur_album or cur_album.strip().lower() == "unknown album":
        new_vals["album"] = album_hint
        changed = True
    if not cur_title:
        new_vals["title"] = fname_title
        changed = True
    if not cur_track and fname_track:
        new_vals["tracknumber"] = fname_track
        changed = True

    if changed:
        print(f"  TAG-FIX {path} -> {new_vals}")
        if execute:
            for k, v in new_vals.items():
                audio[k] = v
            try:
                audio.save()
            except Exception as e:
                print(f"  WARN save failed for {path}: {e}")
                return False
    return changed


def main():
    ap = argparse.ArgumentParser(description="Post-organize cleanup + verify + tag-fix pass")
    ap.add_argument("--music-dir", type=Path, default=Path.home() / "Music")
    ap.add_argument("--manifest", type=Path, default=Path.home() / "music_manifest.json")
    ap.add_argument("--execute", action="store_true", help="Actually delete/fix. Default is report-only.")
    args = ap.parse_args()

    music_dir = args.music_dir.expanduser().resolve()
    if not music_dir.is_dir():
        sys.exit(f"Music dir not found: {music_dir}")

    stats = defaultdict(int)
    hash_map = defaultdict(list)  # digest -> [paths]  (in-tree dedupe pass)

    print(f"=== Pass 1: scanning {music_dir} for stray/broken files ===")
    for path in sorted(music_dir.rglob("*")):
        if path.is_dir():
            continue
        ext = path.suffix.lower()
        name_lower = path.name.lower()

        if name_lower in STRAY_NAMES or ext in STRAY_EXTS:
            stats["stray"] += 1
            print(f"STRAY  {path}")
            if args.execute:
                path.unlink(missing_ok=True)
            continue

        if ext in KEEP_EXTS:
            continue  # cover art, leave alone

        if ext not in AUDIO_EXTS:
            stats["stray"] += 1
            print(f"STRAY  {path}  (non-audio, non-image file in library)")
            if args.execute:
                path.unlink(missing_ok=True)
            continue

        if is_broken_audio(path):
            stats["broken"] += 1
            print(f"BROKEN {path}")
            if args.execute:
                path.unlink(missing_ok=True)
            continue

        try:
            digest = sha256_of(path)
            hash_map[digest].append(path)
        except OSError as e:
            stats["broken"] += 1
            print(f"BROKEN {path}  (unreadable: {e})")
            if args.execute:
                path.unlink(missing_ok=True)

    print(f"\n=== Pass 2: in-tree duplicate check ===")
    for digest, paths in hash_map.items():
        if len(paths) <= 1:
            continue
        paths.sort(key=lambda p: str(p))
        keep, extras = paths[0], paths[1:]
        for extra in extras:
            stats["duplicates"] += 1
            print(f"DUPLICATE {extra}  (identical to kept copy {keep})")
            if args.execute:
                extra.unlink(missing_ok=True)

    print(f"\n=== Pass 3: fill/fix missing tags ===")
    for digest, paths in hash_map.items():
        for path in paths:
            if not path.exists():
                continue  # already removed as a duplicate above
            try:
                rel = path.relative_to(music_dir)
            except ValueError:
                continue
            parts = rel.parts
            artist_hint = parts[0] if len(parts) >= 1 else "Unknown Artist"
            album_hint = parts[1] if len(parts) >= 2 else "Unknown Album"
            if fix_tags(path, artist_hint, album_hint, args.execute):
                stats["tag_fixed"] += 1

    print(f"\n=== Pass 4: prune empty directories ===")
    for dirpath in sorted(music_dir.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if dirpath.is_dir() and not any(dirpath.iterdir()):
            stats["dirs_pruned"] += 1
            print(f"EMPTY-DIR {dirpath}")
            if args.execute:
                dirpath.rmdir()

    if args.manifest.exists():
        print(f"\n=== Pass 5: reconciling manifest {args.manifest} ===")
        manifest = json.loads(args.manifest.read_text())
        cleaned = {}
        for digest, dest in manifest.items():
            if Path(dest).exists():
                cleaned[digest] = dest
            else:
                stats["manifest_orphans"] += 1
                print(f"ORPHAN-ENTRY  {dest}  (no longer on disk, dropping from manifest)")
        if args.execute:
            args.manifest.write_text(json.dumps(cleaned, indent=2, sort_keys=True))

    print(f"\nSummary: stray={stats['stray']} broken={stats['broken']} duplicates={stats['duplicates']} "
          f"tag_fixed={stats['tag_fixed']} dirs_pruned={stats['dirs_pruned']} "
          f"manifest_orphans={stats['manifest_orphans']} mode={'EXECUTE' if args.execute else 'REPORT-ONLY'}")


if __name__ == "__main__":
    main()
