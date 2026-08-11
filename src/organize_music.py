#!/usr/bin/env python3
"""
organize_music.py - Flatten, dedupe, and tag-organize a messy music library.
Idempotent (hash-keyed manifest), self-verifying (post-copy hash check), dry-run by default.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".aiff", ".opus"}


def sha256_of(path: Path, chunk_size=1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize(name: str) -> str:
    for c in '<>:"/\\|?*':
        name = name.replace(c, "_")
    return name.strip() or "Unknown"


def read_tags(path: Path):
    artist = album = title = track = None
    if HAS_MUTAGEN:
        try:
            audio = MutagenFile(path, easy=True)
            if audio:
                artist = (audio.get("artist") or [None])[0]
                album = (audio.get("album") or [None])[0]
                title = (audio.get("title") or [None])[0]
                tn = (audio.get("tracknumber") or [None])[0]
                if tn:
                    track = tn.split("/")[0].strip().zfill(2)
        except Exception:
            pass
    return sanitize(artist or "Unknown Artist"), sanitize(album or "Unknown Album"), sanitize(title or path.stem), track


def find_audio_files(source: Path):
    for p in source.rglob("*"):
        if p.is_file() and p.suffix.lower() in AUDIO_EXTS:
            yield p


def load_manifest(path: Path):
    return json.loads(path.read_text()) if path.exists() else {}


def save_manifest(path: Path, manifest):
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def main():
    ap = argparse.ArgumentParser(description="Flatten + dedupe + tag-organize a music library")
    ap.add_argument("--source", required=True, type=Path)
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--manifest", type=Path, default=Path("music_manifest.json"))
    ap.add_argument("--execute", action="store_true", help="Actually copy files. Default is dry-run.")
    ap.add_argument("--move", action="store_true", help="Delete source after verified copy (implies --execute).")
    args = ap.parse_args()
    if args.move:
        args.execute = True

    source = args.source.expanduser().resolve()
    dest = args.dest.expanduser().resolve()
    if not source.is_dir():
        sys.exit(f"Source not found: {source}")

    manifest = load_manifest(args.manifest)
    seen_hashes = set(manifest.keys())
    planned = duplicates = errors = 0

    for src_file in find_audio_files(source):
        try:
            digest = sha256_of(src_file)
        except OSError as e:
            print(f"ERROR reading {src_file}: {e}")
            errors += 1
            continue

        if digest in seen_hashes:
            duplicates += 1
            print(f"DUP  {src_file}  (already organized as {manifest[digest]})")
            continue

        artist, album, title, track = read_tags(src_file)
        fname = f"{track + ' - ' if track else ''}{title}{src_file.suffix.lower()}"
        dest_path = dest / artist / album / fname

        i = 1
        base_dest = dest_path
        while dest_path.exists():
            if sha256_of(dest_path) == digest:
                break
            dest_path = base_dest.with_stem(f"{base_dest.stem}_{i}")
            i += 1

        planned += 1
        print(f"{'MOVE' if args.move else 'COPY'} {src_file} -> {dest_path}")

        if args.execute:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            if not dest_path.exists():
                shutil.copy2(src_file, dest_path)
                if sha256_of(dest_path) != digest:
                    print(f"VERIFY FAILED for {dest_path}, leaving source intact.")
                    errors += 1
                    continue
            manifest[digest] = str(dest_path)
            seen_hashes.add(digest)
            if args.move:
                src_file.unlink()

    if args.execute:
        save_manifest(args.manifest, manifest)

    print(f"\nSummary: planned={planned} duplicates={duplicates} errors={errors} mode={'EXECUTE' if args.execute else 'DRY-RUN'}")


if __name__ == "__main__":
    main()
