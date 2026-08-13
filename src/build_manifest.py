#!/usr/bin/env python3
"""
ez_jukebox Manifest Builder
Scans audio library and generates a path -> SHA-256 hash manifest.
"""

import os
import sys
import json
import hashlib
import argparse
from pathlib import Path

AUDIO_EXTENSIONS = {'.mp3', '.flac', '.m4a', '.aac', '.ogg', '.wav', '.opus', '.aiff', '.alac'}

def calculate_sha256(filepath, chunk_size=65536):
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        return None

def build_manifest(library_path, output_path):
    library = Path(library_path)
    if not library.exists():
        print(f"❌ Error: Library path '{library_path}' does not exist.")
        return None, None

    print(f"🔍 Scanning {library_path} for audio files...")
    manifest = {}
    indexed_count = 0
    skipped_count = 0

    for root, _, files in os.walk(library):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in AUDIO_EXTENSIONS:
                full_path = os.path.join(root, file)
                file_hash = calculate_sha256(full_path)
                
                if file_hash:
                    manifest[full_path] = file_hash
                    indexed_count += 1
                    if indexed_count % 100 == 0:
                        print(f"   ✓ Indexed {indexed_count} audio files...")
                else:
                    skipped_count += 1

    print(f"\n✅ Indexing complete! Recorded {indexed_count} total file paths ({skipped_count} skipped).")
    return manifest

def write_manifest(manifest, output_path):
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"💾 Manifest written to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing manifest: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="ez_jukebox Manifest Builder")
    parser.add_argument("--library-path", default="/mnt/chromeos/removable/CarterMedia", help="Path to audio library")
    parser.add_argument("--output-path", default="music_manifest.json", help="Path to output JSON manifest")
    args = parser.parse_args()

    manifest = build_manifest(args.library_path, args.output_path)
    if manifest and write_manifest(manifest, args.output_path):
        print("🦆 Done! Library manifest ready for deduplication.")

if __name__ == "__main__":
    main()
