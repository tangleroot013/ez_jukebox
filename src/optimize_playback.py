#!/usr/bin/env python3
# ez_jukebox patch marker: CEREBRO_PATCH_CACHE_V1
"""optimize_playback.py - anti-skip buffer tuning for MPD.

Increases MPD's decoded-audio ring buffer and how much of it fills before
playback starts, so a disk/CPU I/O spike (e.g. opening a new browser tab)
doesn't starve the output thread and cause an audible skip.

Dry-run by default; pass --apply to actually write mpd.conf.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

MPD_PATHS = [
    Path.home() / ".config" / "mpd" / "mpd.conf",
    Path.home() / ".mpd" / "mpd.conf",
    Path("/etc/mpd.conf"),
]

DEFAULT_BUFFER_KB = 32768           # 32 MB - holds ~1-2 FLAC tracks in RAM
DEFAULT_BUFFER_BEFORE_PLAY = "25%"  # fraction of the buffer filled before playback starts


def get_active_mpd_conf() -> Path:
    for path in MPD_PATHS:
        if path.exists():
            return path
    raise FileNotFoundError("no mpd.conf found in " + ", ".join(str(p) for p in MPD_PATHS))


def _current_value(content: str, key: str) -> Optional[str]:
    m = re.search(rf'^\s*{key}\s+(.*)$', content, re.MULTILINE)
    return m.group(1).strip() if m else None


def _backup(path: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_name(path.name + f".bak.{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def apply(buffer_kb: int, buffer_before_play: str, dry_run: bool, restart: bool) -> int:
    try:
        conf_path = get_active_mpd_conf()
    except FileNotFoundError as e:
        print(f"[error] {e}")
        return 1

    try:
        content = conf_path.read_text()
    except PermissionError:
        print(f"[error] no read permission on {conf_path}")
        return 1

    desired = {
        "audio_buffer_size": f'"{buffer_kb}"',
        "buffer_before_play": f'"{buffer_before_play}"',
    }

    changes = {}
    for key, val in desired.items():
        current = _current_value(content, key)
        current_bare = current.strip('"') if current else None
        if current_bare == val.strip('"'):
            print(f"[skip] {key} already set to {val}")
        else:
            changes[key] = val

    if not changes:
        print(f"[done] {conf_path} already tuned, nothing to do")
        return 0

    print(f"[info] target: {conf_path}")
    for key, val in changes.items():
        print(f"[plan] {key} -> {val}")

    if dry_run:
        print("[info] dry-run: no changes written. Re-run with --apply to write them.")
        return 0

    try:
        backup = _backup(conf_path)
    except PermissionError:
        print(f"[error] no write permission to back up {conf_path}")
        return 1
    print(f"[ok] backed up {conf_path} -> {backup}")

    new_content = content
    for key, val in changes.items():
        pattern = re.compile(rf'^\s*{key}\s+.*$', re.MULTILINE)
        if pattern.search(new_content):
            new_content = pattern.sub(f'{key}    {val}', new_content, count=1)
        else:
            new_content += f'\n# Added by ez_jukebox optimize_playback.py\n{key}    {val}\n'

    try:
        conf_path.write_text(new_content)
    except PermissionError:
        print(f"[error] no write permission to {conf_path}")
        return 1

    print(f"[ok] wrote {len(changes)} setting(s) to {conf_path}")

    if restart:
        result = subprocess.run(
            ["systemctl", "--user", "restart", "mpd"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            print("[ok] restarted mpd (systemctl --user restart mpd)")
        else:
            print(f"[error] mpd restart failed: {result.stderr.strip()}")
            print("[info] restart it manually: systemctl --user restart mpd")
            return 1
    else:
        print("[info] restart mpd to apply: systemctl --user restart mpd")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune MPD's audio buffer to prevent I/O-spike skips")
    parser.add_argument("--buffer-kb", type=int, default=DEFAULT_BUFFER_KB,
                         help=f"audio_buffer_size in KiB (default: {DEFAULT_BUFFER_KB})")
    parser.add_argument("--buffer-before-play", default=DEFAULT_BUFFER_BEFORE_PLAY,
                         help=f"buffer_before_play as a percentage (default: {DEFAULT_BUFFER_BEFORE_PLAY})")
    parser.add_argument("--apply", action="store_true",
                         help="write changes to mpd.conf (default is dry-run/preview only)")
    parser.add_argument("--restart", action="store_true",
                         help="restart the mpd user service after applying changes")
    args = parser.parse_args()

    return apply(
        buffer_kb=args.buffer_kb,
        buffer_before_play=args.buffer_before_play,
        dry_run=not args.apply,
        restart=args.restart,
    )


if __name__ == "__main__":
    sys.exit(main())
