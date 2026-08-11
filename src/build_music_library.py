#!/usr/bin/env python3
"""
build_music_library.py - Pull purchased tracks out of Downloads (loose files
AND zip archives), dedupe by content hash, tag-organize into a clean Music
folder. Idempotent, self-verifying, dry-run (scan-only) by default.
"""
import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".wav", ".ogg", ".aac", ".wma", ".aiff", ".opus"}
ARCHIVE_EXTS = {".zip"}
EXCLUDE_DIRS = {"node_modules", ".git", "vendor", "dist", "build", "__pycache__", ".venv"}


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


def clean_album_hint(zip_path: Path) -> str:
    stem = zip_path.stem
    stem = re.sub(r"\(\d+\)$", "", stem).strip()
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return sanitize(stem or "Unknown Album")


def read_tags(path: Path, album_fallback: str = None):
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
    return (
        sanitize(artist or "Unknown Artist"),
        sanitize(album or album_fallback or "Unknown Album"),
        sanitize(title or path.stem),
        track,
    )


def find_loose_audio(root: Path):
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in AUDIO_EXTS:
                yield p, None  # (path, album_fallback)


def find_zip_audio(root: Path):
    """Yield (zip_path, [member_names]) for zips that contain audio members."""
    for dirpath, dirnames, filenames in __import__("os").walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fn in filenames:
            if Path(fn).suffix.lower() not in ARCHIVE_EXTS:
                continue
            zpath = Path(dirpath) / fn
            try:
                with zipfile.ZipFile(zpath) as zf:
                    members = [
                        m for m in zf.namelist()
                        if not m.endswith("/")
                        and not m.startswith("__MACOSX")
                        and Path(m).suffix.lower() in AUDIO_EXTS
                    ]
            except (zipfile.BadZipFile, OSError) as e:
                print(f"WARN unreadable zip {zpath}: {e}")
                continue
            if members:
                yield zpath, members


def load_manifest(path: Path):
    return json.loads(path.read_text()) if path.exists() else {}


def save_manifest(path: Path, manifest):
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def process_file(src_file, album_fallback, dest, manifest, seen_hashes, execute, stats, cleanup=False):
    try:
        digest = sha256_of(src_file)
    except OSError as e:
        print(f"ERROR reading {src_file}: {e}")
        stats["errors"] += 1
        return
    if digest in seen_hashes:
        stats["duplicates"] += 1
        print(f"DUP  {src_file}  (already organized as {manifest[digest]})")
        if cleanup:
            src_file.unlink(missing_ok=True)
        return

    artist, album, title, track = read_tags(src_file, album_fallback)
    fname = f"{track + ' - ' if track else ''}{title}{src_file.suffix.lower()}"
    dest_path = dest / artist / album / fname
    i, base_dest = 1, dest_path
    while dest_path.exists():
        if sha256_of(dest_path) == digest:
            break
        dest_path = base_dest.with_stem(f"{base_dest.stem}_{i}")
        i += 1

    stats["planned"] += 1
    print(f"COPY {src_file} -> {dest_path}")
    if execute:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        if not dest_path.exists():
            shutil.copy2(src_file, dest_path)
            if sha256_of(dest_path) != digest:
                print(f"VERIFY FAILED for {dest_path}")
                stats["errors"] += 1
                return
        manifest[digest] = str(dest_path)
        seen_hashes.add(digest)
        if cleanup:
            src_file.unlink(missing_ok=True)


def main():
    ap = argparse.ArgumentParser(description="Extract + dedupe + tag-organize purchased tracks (loose files and zips)")
    ap.add_argument("--root", type=Path, default=Path("/mnt/chromeos/MyFiles/Downloads"))
    ap.add_argument("--dest", type=Path, default=Path.home() / "Music")
    ap.add_argument("--manifest", type=Path, default=Path.home() / "music_manifest.json")
    ap.add_argument("--execute", action="store_true", help="Actually extract/copy. Default is scan-only.")
    args = ap.parse_args()

    root = args.root.expanduser().resolve()
    dest = args.dest.expanduser().resolve()
    if not root.is_dir():
        sys.exit(f"Root not found: {root}")

    manifest = load_manifest(args.manifest)
    seen_hashes = set(manifest.keys())
    stats = {"planned": 0, "duplicates": 0, "errors": 0}

    print(f"=== Scanning zips under {root} ===")
    for zpath, members in find_zip_audio(root):
        print(f"ZIP {zpath}  ({len(members)} audio file(s))")
        if args.execute:
            album_fallback = clean_album_hint(zpath)
            tmpdir = Path(tempfile.mkdtemp(prefix="musiclib_"))
            with zipfile.ZipFile(zpath) as zf:
                for m in members:
                    try:
                        extracted = zf.extract(m, path=tmpdir)
                        process_file(Path(extracted), album_fallback, dest, manifest, seen_hashes, True, stats, cleanup=True)
                    except Exception as e:
                        print(f"ERROR extracting {m} from {zpath}: {e}")
                        stats["errors"] += 1
            shutil.rmtree(tmpdir, ignore_errors=True)

    print(f"\n=== Scanning loose audio files under {root} ===")
    for src_file, album_fallback in find_loose_audio(root):
        process_file(src_file, album_fallback, dest, manifest, seen_hashes, args.execute, stats)

    if args.execute:
        save_manifest(args.manifest, manifest)

    print(f"\nSummary: planned={stats['planned']} duplicates={stats['duplicates']} "
          f"errors={stats['errors']} mode={'EXECUTE' if args.execute else 'SCAN-ONLY'}")


if __name__ == "__main__":
    main()
