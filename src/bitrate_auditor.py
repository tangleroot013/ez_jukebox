#!/usr/bin/env python3
"""
Bitrate Auditor v1.0
Flags quality outliers and generates album consistency reports.
Quack!
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis

def extract_bitrate(filepath):
    """Extract bitrate from audio file metadata."""
    try:
        if filepath.endswith('.flac'):
            audio = FLAC(filepath)
            # FLAC reports in bits per second; derive from sample rate and bit depth
            return {"format": "FLAC", "lossless": True}
        elif filepath.endswith('.mp3'):
            audio = MP3(filepath)
            return {"format": "MP3", "bitrate_kbps": audio.info.bitrate // 1000, "lossless": False}
        elif filepath.endswith('.ogg'):
            audio = OggVorbis(filepath)
            return {"format": "OGG", "bitrate_kbps": audio.info.bitrate // 1000, "lossless": False}
        else:
            return {"format": "UNKNOWN"}
    except Exception as e:
        return {"format": "ERROR", "error": str(e)}

def audit_library(manifest_path, library_root):
    """Audit library for quality outliers."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    albums = defaultdict(lambda: {"tracks": [], "formats": set(), "bitrates": []})
    
    for track in manifest.get("tracks", []):
        filepath = os.path.join(library_root, track.get("relative_path", ""))
        album = track.get("album", "Unknown")
        
        if not os.path.exists(filepath):
            continue
        
        bitrate_info = extract_bitrate(filepath)
        albums[album]["tracks"].append({
            "title": track.get("title"),
            "path": filepath,
            **bitrate_info
        })
        albums[album]["formats"].add(bitrate_info.get("format"))
        if "bitrate_kbps" in bitrate_info:
            albums[album]["bitrates"].append(bitrate_info["bitrate_kbps"])
    
    # Detect outliers
    outliers = []
    for album, data in albums.items():
        if len(set(data["formats"])) > 1:
            # Mixed formats in one album
            outliers.append({
                "album": album,
                "issue": "MIXED_FORMATS",
                "formats": list(data["formats"]),
                "tracks": data["tracks"]
            })
        
        if data["bitrates"]:
            avg_bitrate = sum(data["bitrates"]) / len(data["bitrates"])
            for track in data["tracks"]:
                if "bitrate_kbps" in track:
                    if track["bitrate_kbps"] < avg_bitrate * 0.5:  # 50% below average
                        outliers.append({
                            "album": album,
                            "issue": "LOW_BITRATE",
                            "track": track["title"],
                            "bitrate_kbps": track["bitrate_kbps"],
                            "album_avg": round(avg_bitrate)
                        })
    
    return outliers

def main():
    manifest = "music_manifest.json"
    library_root = "/home/tangleroot013/Music-library"  # Default path
    
    if len(sys.argv) > 1:
        library_root = sys.argv[1]
    
    print(f"🦆 Bitrate Auditor | Analyzing {library_root}...")
    outliers = audit_library(manifest, library_root)
    
    if not outliers:
        print("\n✅ No quality outliers detected. Your library is consistent. Quack!")
        sys.exit(0)
    
    print(f"\n⚠️  QUALITY OUTLIERS DETECTED ({len(outliers)} issues):\n")
    for item in outliers:
        if item["issue"] == "MIXED_FORMATS":
            print(f"   📀 ALBUM: {item['album']}")
            print(f"      Mixed formats: {', '.join(item['formats'])}")
        elif item["issue"] == "LOW_BITRATE":
            print(f"   📀 ALBUM: {item['album']}")
            print(f"      Track: {item['track']} ({item['bitrate_kbps']} kbps vs {item['album_avg']} avg)")
    
    sys.exit(1)

if __name__ == "__main__":
    main()
