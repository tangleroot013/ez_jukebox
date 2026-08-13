#!/usr/bin/env python3
# ==============================================================================
# ez_jukebox - Content-Based Manifest Generator
# ==============================================================================
"""
Walks an external music library directory, computes SHA-256 hashes of all audio
file contents, detects duplicate tracks, and outputs a clean music_manifest.json.
"""

import json
import hashlib
import os
import sys
from pathlib import Path
from collections import defaultdict

DEFAULT_DRIVE_PATH = "/mnt/chromeos/removable/CarterMedia"
DEFAULT_MANIFEST_OUT = os.path.expanduser("~/github_projects/ez_jukebox/music_manifest.json")
AUDIO_EXTS = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg', '.opus', '.alac'}

def hash_file_content(filepath: str, chunk_size: int = 65536) -> str | None:
    """Compute SHA-256 hash of file content in chunks (memory-efficient)."""
    sha = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha.update(chunk)
        return sha.hexdigest()
    except (OSError, IOError) as e:
        print(f"⚠️ Skipped {filepath}: {e}")
        return None

def scan_and_build_manifest(drive_path: str):
    """Walk drive, hash audio files, return manifest dict and duplicates."""
    manifest = {}
    duplicates = defaultdict(list)
    skipped = 0
    total = 0

    print(f"🔍 Scanning {drive_path} for audio files...")

    for root, _, files in os.walk(drive_path):
        for file in files:
            total += 1
            filepath = os.path.join(root, file)
            ext = Path(file).suffix.lower()

            if ext not in AUDIO_EXTS:
                continue

            file_hash = hash_file_content(filepath)
            if not file_hash:
                skipped += 1
                continue

            if file_hash in manifest:
                duplicates[file_hash].append(filepath)
            else:
                manifest[file_hash] = filepath

            if len(manifest) % 100 == 0 and len(manifest) > 0:
                print(f"   ✓ Indexed {len(manifest)} unique audio files...")

    return manifest, duplicates, skipped

def main():
    drive_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DRIVE_PATH
    manifest_out = DEFAULT_MANIFEST_OUT

    if not os.path.exists(drive_path):
        print(f"❌ Error: Drive path '{drive_path}' does not exist or is not shared with Linux.")
        sys.exit(1)

    manifest, dups, skipped = scan_and_build_manifest(drive_path)

    if manifest:
        os.makedirs(os.path.dirname(manifest_out), exist_ok=True)
        with open(manifest_out, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        print(f"\n✅ Manifest successfully saved to: {manifest_out}")
        print(f"   🎵 Unique tracks indexed: {len(manifest)}")
        print(f"   ⚠️ Skipped/unreadable files: {skipped}")
        if dups:
            print(f"   🔄 Duplicate content hashes detected: {len(dups)}")
            for hash_key, paths in list(dups.items())[:3]:
                print(f"      • {hash_key[:16]}... → {len(paths)} duplicate copies")
    else:
        print(f"❌ No supported audio files found in {drive_path}")

if __name__ == "__main__":
    main()
