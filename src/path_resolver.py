#!/usr/bin/env python3
# ez_jukebox patch marker: CEREBRO_PATCH_CACHE_V1
"""Locate, cache, and validate candidate music library roots on ChromeOS/Crostini.

Crostini mounts external/removable media under /mnt/chromeos/removable/<label>
and the shared "My files" folder under /mnt/chromeos/MyFiles/. This scans
those locations (plus any explicit candidates) for directories that actually
look like a music library, rather than trusting a single hardcoded or
symlinked path.

Adds a JSON cache so repeat lookups (e.g. every `jukebox play`) don't re-walk
every mount point, and a fallback directory so MPD never fails to start just
because a USB drive is unplugged.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

AUDIO_EXTS = {".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav", ".aac", ".wma"}
CROSTINI_REMOVABLE = Path("/mnt/chromeos/removable")
CROSTINI_MYFILES = Path("/mnt/chromeos/MyFiles")
KNOWN_BAD_TARGETS = {"Downloads"}

CONFIG_DIR = Path.home() / ".config" / "ez_jukebox"
CACHE_FILE = CONFIG_DIR / "path_cache.json"
FALLBACK_DIR = CONFIG_DIR / "fallback_library"


@dataclass
class Candidate:
    path: Path
    audio_file_count: int
    is_symlink: bool
    symlink_target: Optional[Path]

    @property
    def looks_valid(self) -> bool:
        if self.audio_file_count == 0:
            return False
        if self.symlink_target and self.symlink_target.name in KNOWN_BAD_TARGETS:
            return False
        return True


def _count_audio_files(root: Path, sample_limit: int = 500) -> int:
    count = 0
    try:
        for p in root.rglob("*"):
            if p.suffix.lower() in AUDIO_EXTS:
                count += 1
                if count >= sample_limit:
                    break
    except (PermissionError, OSError):
        pass
    return count


def _inspect(path: Path) -> Optional[Candidate]:
    if not path.exists() or not path.is_dir():
        return None
    is_link = path.is_symlink()
    target = path.resolve() if is_link else None
    return Candidate(
        path=path,
        audio_file_count=_count_audio_files(path),
        is_symlink=is_link,
        symlink_target=target,
    )


def find_candidates(extra_paths: Optional[list] = None) -> list:
    roots = []
    if CROSTINI_REMOVABLE.exists():
        roots.extend(p for p in CROSTINI_REMOVABLE.iterdir() if p.is_dir())
    if CROSTINI_MYFILES.exists():
        roots.extend(p for p in CROSTINI_MYFILES.iterdir() if p.is_dir())
    home_music = Path.home() / "Music"
    if home_music.exists():
        roots.append(home_music)
    for extra in extra_paths or []:
        roots.append(Path(extra).expanduser())

    candidates = []
    seen = set()
    for root in roots:
        resolved = root.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        c = _inspect(root)
        if c:
            candidates.append(c)
    return candidates


def get_active_library(force_scan: bool = False, extra_paths: Optional[list] = None) -> Path:
    """Return the best library path. Uses a cache to avoid a full rescan on every call."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not force_scan and CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text())
            cached_path = Path(data.get("path", ""))
            if cached_path.is_dir() and cached_path != FALLBACK_DIR:
                return cached_path
        except (json.JSONDecodeError, OSError):
            pass

    candidates = find_candidates(extra_paths)
    valid = [c for c in candidates if c.looks_valid]

    if valid:
        best = max(valid, key=lambda c: c.audio_file_count)
        try:
            CACHE_FILE.write_text(json.dumps({"path": str(best.path)}))
        except OSError:
            pass
        return best.path

    # No real media found (e.g. USB unplugged) - fall back so MPD doesn't
    # crash on startup, but never cache the fallback as if it were real,
    # so the next call still tries a real scan instead of getting stuck.
    FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    return FALLBACK_DIR


def main() -> int:
    parser = argparse.ArgumentParser(description="Find candidate music library roots")
    parser.add_argument("--path", action="append", dest="extra_paths",
                         help="additional path to check, can repeat")
    parser.add_argument("--quiet", action="store_true", help="only print the best path, or nothing")
    parser.add_argument("--force-scan", action="store_true", help="ignore cache and force a rescan")
    args = parser.parse_args()

    if args.quiet:
        print(get_active_library(args.force_scan, args.extra_paths))
        return 0

    candidates = find_candidates(args.extra_paths)
    if not candidates:
        print("No candidate directories found under Crostini mount points.", file=sys.stderr)
    else:
        print(f"{'PATH':<50} {'AUDIO FILES':>12}  STATUS")
        for c in sorted(candidates, key=lambda c: c.audio_file_count, reverse=True):
            status = "OK" if c.looks_valid else "SKIP"
            if c.is_symlink and c.symlink_target and c.symlink_target.name in KNOWN_BAD_TARGETS:
                status += f" (symlink -> {c.symlink_target}, looks wrong)"
            print(f"{str(c.path):<50} {c.audio_file_count:>12}  {status}")

    best = get_active_library(args.force_scan, args.extra_paths)
    if best == FALLBACK_DIR:
        print(f"\nWarning: no real library found, falling back to {best}", file=sys.stderr)
        return 1
    print(f"\nActive library: {best} (cached for future runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
