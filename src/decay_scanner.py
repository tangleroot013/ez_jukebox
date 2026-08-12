#!/usr/bin/env python3
"""
Digital Decay Scanner v1.0
Detects file corruption, truncation, and metadata mismatches in your music library.
Quack!
"""

import json
import os
import hashlib
import sys
from pathlib import Path
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.oggvorbis import OggVorbis
from mutagen.oggflac import OggFLAC

def calculate_sha256(filepath, chunk_size=65536):
    """Calculate SHA256 checksum of file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        return None

def probe_file_header(filepath):
    """Probe file header for corruption/truncation."""
    try:
        size = os.path.getsize(filepath)
        if size < 1024:  # Suspiciously small
            return {"status": "TRUNCATED", "size_bytes": size}
        
        # Try to load metadata
        if filepath.endswith('.flac'):
            audio = FLAC(filepath)
        elif filepath.endswith('.mp3'):
            audio = MP3(filepath)
        elif filepath.endswith('.ogg'):
            audio = OggVorbis(filepath)
        else:
            return {"status": "UNSUPPORTED"}
        
        return {
            "status": "OK",
            "duration_seconds": audio.info.length,
            "bitrate": getattr(audio.info, 'bitrate', 'N/A')
        }
    except Exception as e:
        return {"status": "CORRUPTED", "error": str(e)}

def scan_library(manifest_path, library_root):
    """Scan entire library against manifest."""
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    report = {
        "scanned": 0,
        "ok": 0,
        "corrupted": [],
        "truncated": [],
        "missing": [],
        "checksum_mismatches": []
    }
    
    for track in manifest.get("tracks", []):
        filepath = os.path.join(library_root, track.get("relative_path", ""))
        report["scanned"] += 1
        
        # Check if file exists
        if not os.path.exists(filepath):
            report["missing"].append({"track": track.get("title"), "path": filepath})
            continue
        
        # Probe header
        probe = probe_file_header(filepath)
        if probe["status"] != "OK":
            if probe["status"] == "TRUNCATED":
                report["truncated"].append({"track": track.get("title"), "size_bytes": probe["size_bytes"]})
            elif probe["status"] == "CORRUPTED":
                report["corrupted"].append({"track": track.get("title"), "error": probe.get("error")})
            continue
        
        # Checksum validation (optional, if manifest includes checksums)
        if "checksum" in track:
            current_checksum = calculate_sha256(filepath)
            if current_checksum != track["checksum"]:
                report["checksum_mismatches"].append({
                    "track": track.get("title"),
                    "expected": track["checksum"],
                    "actual": current_checksum
                })
                continue
        
        report["ok"] += 1
    
    return report

def main():
    manifest = "music_manifest.json"
    library_root = "/home/tangleroot013/Music-library"  # Default path
    
    if len(sys.argv) > 1:
        library_root = sys.argv[1]
    
    print(f"🦆 Digital Decay Scanner | Scanning {library_root}...")
    report = scan_library(manifest, library_root)
    
    print(f"\n📊 SCAN REPORT")
    print(f"   Total Scanned: {report['scanned']}")
    print(f"   ✅ Healthy: {report['ok']}")
    print(f"   🔴 Corrupted: {len(report['corrupted'])}")
    print(f"   ⚠️  Truncated: {len(report['truncated'])}")
    print(f"   ❌ Missing: {len(report['missing'])}")
    print(f"   🔄 Checksum Mismatches: {len(report['checksum_mismatches'])}")
    
    if report['corrupted']:
        print(f"\n⚠️  CORRUPTED FILES:")
        for item in report['corrupted'][:10]:
            print(f"   - {item['track']}: {item['error']}")
    
    if report['missing']:
        print(f"\n❌ MISSING FILES:")
        for item in report['missing'][:10]:
            print(f"   - {item['track']}")
    
    # Exit with failure if issues found
    if report['corrupted'] or report['truncated'] or report['missing']:
        sys.exit(1)
    else:
        print("\n✅ All systems nominal. Quack!")
        sys.exit(0)

if __name__ == "__main__":
    main()
