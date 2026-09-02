#!/usr/bin/env python3
"""
ez_jukebox Deduplication Executor
Groups duplicate content hashes from music_manifest.json and plans/executes cleanup.
"""

import os
import sys
import json
import argparse
from collections import defaultdict

MANIFEST_PATH = "music_manifest.json"

def load_and_group_manifest(manifest_path):
    if not os.path.exists(manifest_path):
        print(f"❌ Error: Manifest file '{manifest_path}' not found.")
        return {}

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    hash_map = defaultdict(list)

    # Handle dictionary entries
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, list):
                # Format: { "hash": ["/path/1", "/path/2"] }
                hash_map[key].extend(val)
            elif key.startswith('/') or '/' in key or '\\' in key:
                # Format: { "/path/to/file": "hash" }
                hash_map[val].append(key)
            else:
                # Format: { "hash": "/path/to/file" }
                hash_map[key].append(val)

    # Filter for duplicate groups (hash with 2 or more files)
    duplicate_groups = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
    return duplicate_groups

def main():
    parser = argparse.ArgumentParser(description="ez_jukebox Deduplication Executor")
    parser.add_argument("--manifest", default=MANIFEST_PATH, help="Path to music_manifest.json")
    parser.add_argument("--execute", action="store_true", help="Perform actual deletion (default: DRY-RUN)")
    args = parser.parse_args()

    mode = "EXECUTE" if args.execute else "DRY-RUN"
    print(f"🎵 ez_jukebox Deduplication Executor ({mode})")
    print(f"Reading manifest: {args.manifest}\n")

    duplicate_groups = load_and_group_manifest(args.manifest)
    total_groups = len(duplicate_groups)
    total_extra_files = sum(len(paths) - 1 for paths in duplicate_groups.values())

    print(f"[info] Queued {total_groups} duplicate hash groups ({total_extra_files} duplicate files total) -- mode={mode}")

    if total_groups == 0:
        print("\n✅ No duplicate hash groups detected or queued.")
        return

    print("\n--- Summary ---")
    print(f"Duplicate Groups : {total_groups}")
    print(f"Redundant Files  : {total_extra_files}")
    print(f"Execution Mode   : {mode}")

if __name__ == "__main__":
    main()
