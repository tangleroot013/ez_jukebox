#!/usr/bin/env python3
"""
EZ Jukebox Track Selector

Filters manifest tracks by existence, readability, and history buffer.
Handles both JSON list format and {"tracks": [...]} dictionary format.
Supports robust CLI flag and positional argument parsing via argparse.
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path
from typing import Optional


def select_track(
    manifest_path: Path,
    history_file: Path,
    max_history: int,
    output_file: Optional[Path] = None,
) -> None:
    """Selects an unplayed, verified audio file from the manifest and logs it to history."""
    if not manifest_path.exists():
        sys.exit(1)

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tracks = data if isinstance(data, list) else data.get("tracks", [])
    except Exception:
        sys.exit(1)

    history = []
    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = [line.strip() for line in f if line.strip()]
        except Exception:
            history = []

    # Filter candidates: must be valid dict, readable file on disk, not in history
    candidates = [
        t["file"]
        for t in tracks
        if isinstance(t, dict)
        and t.get("file")
        and os.path.isfile(t["file"])
        and os.access(t["file"], os.R_OK)
        and t["file"] not in history
    ]

    # Fallback: prune oldest half of history buffer if candidate pool is exhausted
    if not candidates and history:
        history = history[len(history) // 2 :]
        candidates = [
            t["file"]
            for t in tracks
            if isinstance(t, dict)
            and t.get("file")
            and os.path.isfile(t["file"])
            and os.access(t["file"], os.R_OK)
            and t["file"] not in history
        ]

    if candidates:
        selected = random.choice(candidates)
        history.append(selected)
        history = history[-max_history:]

        try:
            history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(history_file, "w", encoding="utf-8") as f:
                f.write("\n".join(history) + "\n")
        except Exception:
            pass

        if output_file:
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(selected + "\n")
            except Exception:
                pass

        print(selected)
    else:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="EZ Jukebox Track Selector with flexible CLI argument support"
    )

    # Positional arguments (backward compatibility)
    parser.add_argument(
        "pos_manifest",
        nargs="?",
        type=Path,
        help="Path to music manifest JSON file",
    )
    parser.add_argument(
        "pos_history", nargs="?", type=Path, help="Path to history file"
    )
    parser.add_argument(
        "pos_max_history", nargs="?", type=int, help="Maximum history count"
    )

    # Optional flagged arguments
    parser.add_argument(
        "-m", "--manifest", type=Path, help="Path to music manifest JSON file"
    )
    parser.add_argument(
        "-H", "--history", type=Path, help="Path to history file"
    )
    parser.add_argument(
        "-c", "--max-history", type=int, help="Maximum history count"
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Optional path to write selected track location",
    )

    args, unknown = parser.parse_known_args()

    manifest = args.manifest or args.pos_manifest
    history = args.history or args.pos_history
    max_history = (
        args.max_history
        if args.max_history is not None
        else (
            args.pos_max_history if args.pos_max_history is not None else 50
        )
    )

    if not manifest or not history or max_history is None:
        sys.exit(1)

    select_track(manifest, history, max_history, args.output)


if __name__ == "__main__":
    main()
