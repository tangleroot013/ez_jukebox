#!/usr/bin/env python3
"""
Sample Rate Sentinel v1.0
Detects high-res files being resampled and reports wasted storage.
Quack!
"""

import json
import os
import sys
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

def extract_sample_rate(filepath):
    """Extract sample rate from audio file."""
    try:
        if filepath.endswith('.flac'):
            audio = FLAC(filepath)
            return audio.info.sample_rate
        elif filepath.endswith('.mp3'):
            audio = MP3(filepath)
            return audio.info.sample_rate
        elif filepath.endswith('.ogg'):
            audio = OggVorbis(filepath)
            return audio.info.sample_rate
        else:
            return None
    except Exception as e:
        return None

def scan_for_highres(manifest_path, library_root, mpd_max_rate=48000):
    """Scan for high-res files and estimate wasted storage."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    highres_files = []
    total_highres_size = 0
    
    for track in manifest.get("tracks", []):
        filepath = os.path.join(library_root, track.get("relative_path", ""))
        
        if not os.path.exists(filepath):
            continue
        
        sample_rate = extract_sample_rate(filepath)
        if sample_rate and sample_rate > mpd_max_rate:
            file_size = os.path.getsize(filepath) / (1024**3)  # GB
            total_highres_size += file_size
            highres_files.append({
                "title": track.get("title"),
                "album": track.get("album"),
                "sample_rate": sample_rate,
                "size_gb": round(file_size, 2)
            })
    
    return highres_files, total_highres_size

def main():
    manifest = "music_manifest.json"
    library_root = "/home/tangleroot013/Music-library"  # Default path
    
    if len(sys.argv) > 1:
        library_root = sys.argv[1]
    
    print(f"🦆 Sample Rate Sentinel | Scanning {library_root}...")
    highres_files, total_size = scan_for_highres(manifest, library_root)
    
    if not highres_files:
        print("\n✅ No high-res files detected. All files ≤ 48kHz. Quack!")
        sys.exit(0)
    
    print(f"\n⚠️  HIGH-RES FILES DETECTED ({len(highres_files)} files, {total_size:.2f} GB total):")
    print(f"    These will be resampled to 48kHz by Crostini.\n")
    
    for item in highres_files[:20]:
        print(f"   {item['sample_rate']}kHz | {item['size_gb']}GB | {item['album']} - {item['title']}")
    
    if len(highres_files) > 20:
        print(f"   ... and {len(highres_files) - 20} more.")
    
    print(f"\n💾 STORAGE INSIGHT:")
    print(f"   Total high-res storage: {total_size:.2f} GB")
    print(f"   Recommendation: Consider transcoding to FLAC 48kHz to free up space.")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
