#!/usr/bin/env python3
"""
🦆 Sample Rate Sentinel | Identifies high-res files (>48kHz) bottlenecked by Crostini
Calculates wasted storage from unnecessary upsampling
Supports hash-to-filepath dictionaries, flat lists, and {"tracks": [...]} formats
"""

import json
import os
import sys
from argparse import ArgumentParser, SUPPRESS
from mutagen import File

def parse_manifest(manifest_path):
    """
    Parse music_manifest.json in multiple formats:
    - Hash mapping: {"hash": "filepath", ...}
    - Flat list: ["path1", "path2"]
    - Dict with tracks: {"tracks": ["path1", "path2"]}
    """
    if not os.path.exists(manifest_path):
        return []
    
    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []
    
    paths = []
    
    if isinstance(data, dict):
        if "tracks" in data and isinstance(data["tracks"], list):
            # {"tracks": [...]}
            paths = data["tracks"]
        else:
            # {"hash": "filepath", ...} — extract values only
            paths = list(data.values())
    elif isinstance(data, list):
        # Flat list
        paths = data
    
    # Flatten and filter strings only
    return [p for p in paths if isinstance(p, str)]


def rebase_path(original_path, default_root="/home/tangleroot013/Music-library"):
    """
    If path points to default_root, remap to MUSIC_ROOT or actual library.
    Otherwise return path as-is.
    """
    music_root = os.getenv("MUSIC_ROOT", default_root)
    
    if original_path.startswith(default_root) and music_root != default_root:
        # Rebase: /home/.../Music-library/Artist/Album/Song.mp3 → /mnt/.../CarterMedia/Artist/Album/Song.mp3
        relative = original_path[len(default_root):].lstrip("/")
        rebased = os.path.join(music_root, relative)
        return rebased
    
    return original_path


def get_sample_rate(filepath):
    """Extract sample rate from audio file (Hz). Returns None on failure."""
    try:
        audio = File(filepath)
        if audio is None:
            return None
        
        if hasattr(audio.info, 'sample_rate'):
            return audio.info.sample_rate
    except Exception:
        pass
    
    return None


def format_bytes(bytes_val):
    """Convert bytes to human-readable format (MB/GB)"""
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def main():
    parser = ArgumentParser(add_help=False)
    parser.add_argument("library_path", nargs="?", default="", help=SUPPRESS)
    args, _ = parser.parse_known_args()
    
    library_root = args.library_path or os.getenv("MUSIC_ROOT", "/home/tangleroot013/Music-library")
    manifest_path = os.path.join(os.path.dirname(__file__), "..", "music_manifest.json")
    
    print(f"🦆 Sample Rate Sentinel | Scanning {library_root}...\n")
    
    paths = parse_manifest(manifest_path)
    paths = [rebase_path(p, "/home/tangleroot013/Music-library") for p in paths]
    
    if not paths:
        print("✅ No high-res files detected. All files ≤ 48kHz. Quack!")
        return
    
    high_res_files = []
    standard_files = []
    total_wasted_bytes = 0
    scanned_count = 0
    
    for path in paths:
        if not os.path.exists(path):
            continue
        
        sample_rate = get_sample_rate(path)
        if sample_rate is None:
            continue
        
        scanned_count += 1
        file_size_bytes = os.path.getsize(path)
        
        if sample_rate > 48000:
            # Estimate wasted storage: (sample_rate - 48kHz) / sample_rate * file_size
            excess_factor = (sample_rate - 48000) / sample_rate
            wasted_bytes = int(file_size_bytes * excess_factor)
            total_wasted_bytes += wasted_bytes
            high_res_files.append((path, sample_rate, wasted_bytes))
        else:
            standard_files.append((path, sample_rate))
    
    # Print report
    print(f"📊 HIGH-RES SCAN REPORT")
    print(f"   Total Scanned: {scanned_count}")
    print(f"   ✅ Standard (≤48kHz): {len(standard_files)}")
    print(f"   🎵 High-Res (>48kHz): {len(high_res_files)}")
    print(f"   💾 Wasted Storage: {format_bytes(total_wasted_bytes)}")
    
    if high_res_files:
        print(f"\n⚠️  High-Res Files Detected ({len(high_res_files)} tracks):")
        for path, sr, wasted in sorted(high_res_files, key=lambda x: x[2], reverse=True)[:10]:
            sr_khz = sr / 1000
            print(f"   {os.path.basename(path)}: {sr_khz:.1f} kHz ({format_bytes(wasted)} wasted)")
        if len(high_res_files) > 10:
            print(f"   ... and {len(high_res_files) - 10} more")
        print(f"\n💡 Tip: Crostini's audio resampler (soxr) caps at 48kHz. Consider downsampling high-res files.")
    else:
        print(f"\n✅ No high-res files detected. All files ≤ 48kHz. Quack!")


if __name__ == "__main__":
    main()
