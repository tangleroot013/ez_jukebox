#!/usr/bin/env python3
import json
import sys
import random
import argparse
from pathlib import Path

def select_track(manifest_path: Path, history_path: Path, max_history: int, output_path: Path = None, debug: bool = False) -> None:
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        if debug:
            print(f"[DEBUG] Failed to load manifest: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract file paths from the "files" dict
    all_tracks = list(data.get('files', {}).keys())
    
    if debug:
        print(f"[DEBUG] Loaded {len(all_tracks)} tracks from manifest", file=sys.stderr)

    # Load history
    history = set()
    if history_path.exists():
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history = {line.strip() for line in f if line.strip()}
        except Exception as e:
            if debug:
                print(f"[DEBUG] Failed to load history: {e}", file=sys.stderr)

    if debug:
        print(f"[DEBUG] History size: {len(history)}", file=sys.stderr)

    # Get candidates (tracks not in recent history)
    candidates = [t for t in all_tracks if t not in history]

    if debug:
        print(f"[DEBUG] Found {len(candidates)} candidates (after history filter)", file=sys.stderr)

    if not candidates:
        if debug:
            print("[DEBUG] No candidates available!", file=sys.stderr)
        sys.exit(1)

    # Select random track
    selected = random.choice(candidates)

    if debug:
        print(f"[DEBUG] Selected: {selected}", file=sys.stderr)

    # Append to history, keep only last max_history entries
    history_list = list(history) + [selected]
    history_list = history_list[-max_history:]

    try:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with open(history_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(history_list) + '\n')
    except Exception as e:
        if debug:
            print(f"[DEBUG] Failed to write history: {e}", file=sys.stderr)

    # Write output file if requested
    if output_path:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(selected + '\n')
        except Exception:
            pass

    print(selected)

def main() -> None:
    parser = argparse.ArgumentParser(description="EZ Jukebox Track Selector")
    parser.add_argument("pos_manifest", nargs="?", type=Path, help="Path to music manifest JSON file")
    parser.add_argument("pos_history", nargs="?", type=Path, help="Path to history file")
    parser.add_argument("pos_max_history", nargs="?", type=int, help="Maximum history count")
    parser.add_argument("-m", "--manifest", type=Path, help="Path to music manifest JSON file")
    parser.add_argument("-H", "--history", type=Path, help="Path to history file")
    parser.add_argument("-c", "--max-history", type=int, help="Maximum history count")
    parser.add_argument("-o", "--output", type=Path, help="Optional path to write selected track location")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug output")

    args, unknown = parser.parse_known_args()

    manifest = args.manifest or args.pos_manifest
    history = args.history or args.pos_history
    max_history = args.max_history if args.max_history is not None else (args.pos_max_history if args.pos_max_history is not None else 50)

    if not manifest or not history or max_history is None:
        sys.exit(1)

    select_track(manifest, history, max_history, args.output, debug=args.debug)

if __name__ == "__main__":
    main()
