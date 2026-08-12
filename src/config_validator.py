#!/usr/bin/env python3
# ez_jukebox patch marker: CEREBRO_PATCH_CACHE_V1
"""Sanity-check ez_jukebox's mpd.conf and ncmpcpp config before 'just setup'.

Catches two failure modes that bite silently:
  1. music_directory pointing at a symlink that resolves somewhere useless
     (like ChromeOS Downloads) instead of the real consolidated library.
  2. mpd.conf and ncmpcpp's mpd_music_dir drifting out of sync.

--fix resolves the active library via path_resolver.get_active_library()
and rewrites both config files to match, backing up originals first.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from path_resolver import FALLBACK_DIR, get_active_library  # noqa: E402

MPD_CONF = Path.home() / ".config/mpd/mpd.conf"
NCMPCPP_CONF = Path.home() / ".ncmpcpp/config"
KNOWN_BAD_TARGETS = {"Downloads"}


def _extract_quoted(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(1) if m else None


def _extract_kv(pattern: str, text: str) -> Optional[str]:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else None


def check() -> list:
    problems = []

    if not MPD_CONF.exists():
        problems.append(f"missing {MPD_CONF} - run 'just setup' first")
        return problems

    mpd_text = MPD_CONF.read_text()
    mpd_dir_raw = _extract_quoted(r'music_directory\s+"([^"]+)"', mpd_text)
    if not mpd_dir_raw:
        problems.append("mpd.conf has no music_directory set")
        return problems

    mpd_dir = Path(mpd_dir_raw).expanduser()
    if not mpd_dir.exists():
        problems.append(f"mpd.conf music_directory does not exist: {mpd_dir}")
    elif mpd_dir.is_symlink():
        target = mpd_dir.resolve()
        if target.name in KNOWN_BAD_TARGETS:
            problems.append(
                f"mpd.conf music_directory ({mpd_dir}) is a symlink to "
                f"{target}, which looks like the wrong place"
            )

    if NCMPCPP_CONF.exists():
        ncmpcpp_text = NCMPCPP_CONF.read_text()
        ncmpcpp_dir_raw = _extract_kv(r'mpd_music_dir\s*=\s*(.+)', ncmpcpp_text)
        if ncmpcpp_dir_raw:
            ncmpcpp_dir = Path(ncmpcpp_dir_raw.strip()).expanduser()
            if ncmpcpp_dir.resolve() != mpd_dir.resolve():
                problems.append(
                    f"mismatch: mpd.conf points at {mpd_dir}, "
                    f"ncmpcpp config points at {ncmpcpp_dir}"
                )
    else:
        problems.append(f"missing {NCMPCPP_CONF} - run 'just setup' first")

    return problems


def _backup(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%dT%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak.{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def fix() -> int:
    resolved = get_active_library()
    if resolved == FALLBACK_DIR:
        print("[error] no real music library found - refusing to write a fallback "
              "path into mpd.conf. Plug in your media and run "
              "'bin/jukebox resolve --force-scan' first.")
        return 1

    if not MPD_CONF.exists():
        print(f"[error] {MPD_CONF} does not exist - run 'just setup' first")
        return 1

    mpd_text = MPD_CONF.read_text()
    if re.search(rf'music_directory\s+"{re.escape(str(resolved))}"', mpd_text):
        print(f"[skip] mpd.conf music_directory already points at {resolved}")
    else:
        backup = _backup(MPD_CONF)
        new_text, n = re.subn(
            r'music_directory\s+"[^"]*"',
            f'music_directory    "{resolved}"',
            mpd_text,
            count=1,
        )
        if n == 0:
            print("[error] could not find a music_directory line to replace in mpd.conf")
            return 1
        MPD_CONF.write_text(new_text)
        print(f"[ok] mpd.conf music_directory -> {resolved} (backup: {backup})")

    if NCMPCPP_CONF.exists():
        ncmpcpp_text = NCMPCPP_CONF.read_text()
        if re.search(rf'mpd_music_dir\s*=\s*{re.escape(str(resolved))}\s*$', ncmpcpp_text, re.M):
            print(f"[skip] ncmpcpp config mpd_music_dir already points at {resolved}")
        else:
            backup = _backup(NCMPCPP_CONF)
            new_text, n = re.subn(
                r'mpd_music_dir\s*=\s*.*',
                f'mpd_music_dir = {resolved}',
                ncmpcpp_text,
                count=1,
           )
            if n == 0:
                print("[skip] no mpd_music_dir line in ncmpcpp config to replace (leaving as-is)")
            else:
                NCMPCPP_CONF.write_text(new_text)
                print(f"[ok] ncmpcpp mpd_music_dir -> {resolved} (backup: {backup})")
    else:
        print(f"[skip] {NCMPCPP_CONF} does not exist, nothing to fix there")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ez_jukebox config alignment")
    parser.add_argument("--fix", action="store_true",
                         help="auto-resolve the active library and rewrite mpd.conf / ncmpcpp config")
    args = parser.parse_args()

    if args.fix:
        return fix()

    problems = check()
    if not problems:
        print("OK: mpd.conf and ncmpcpp config are consistent and point at a real directory.")
        return 0
    print("Config problems found:")
    for p in problems:
        print(f"  - {p}")
    print("\nRun 'bin/jukebox validate --fix' to auto-resolve and rewrite these paths.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
