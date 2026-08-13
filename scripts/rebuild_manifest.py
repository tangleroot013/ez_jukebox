#!/usr/bin/env python3
"""
rebuild_manifest.py - rescan music roots and write fresh music_manifest.json
{path: sha256} schema, audio files only -- skips .png/.webm/.vtt sidecars,
quarantine folders, and non-audio extensions.

Usage:
  python3 scripts/rebuild_manifest.py                         # default roots
  python3 scripts/rebuild_manifest.py /root1 /root2 ...       # explicit roots
"""
import hashlib, json, sys, time
from pathlib import Path
from collections import Counter

AUDIO_EXTS = {".mp3", ".flac", ".ogg", ".m4a", ".opus", ".wav", ".aac"}
DEFAULT_ROOTS = [
    Path.home() / "Music-library",
    Path("/mnt/chromeos/removable/CarterMedia/Music"),
]
SKIP_DIRS = {"_quarantine", "_dedup_quarantine", "$RECYCLE.BIN"}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    roots = [Path(r) for r in sys.argv[1:]] if len(sys.argv) > 1 else DEFAULT_ROOTS
    roots = [r for r in roots if r.exists()]
    
    if not roots:
        print(f"[error] no valid roots found -- checked: {DEFAULT_ROOTS}")
        sys.exit(1)
        
    print(f"[info] scanning {len(roots)} root(s)")
    for r in roots:
        print(f"         {r}")

    manifest = {}
    scanned = skipped = errors = 0
    start_time = time.time()
    
    for root in roots:
        for f in root.rglob("*"):
            if not f.is_file():
                continue
            if any(part in SKIP_DIRS for part in f.parts):
                skipped += 1
                continue
            if f.suffix.lower() not in AUDIO_EXTS:
                skipped += 1
                continue
            try:
                manifest[str(f)] = sha256(f)
                scanned += 1
                if scanned % 1000 == 0:
                    print(f"[info] {scanned} files hashed...")
            except Exception as e:
                print(f"[error] {f}: {e}")
                errors += 1

    # Metadata wrap
    output_data = {  
        "metadata": {        
            "version": "2.1",         
            "timestamp": time.ctime(),
            "root_count": len(roots)
        },                
        "files": manifest
    }

    # Write manifest to the project root, not the scripts folder        
    out_path = Path("music_manifest.json")
    if out_path.exists():                          
        backup = out_path.with_suffix(".json.bak")
        out_path.rename(backup)                
        print(f"[ok] backup created: {backup}")

    out_path.write_text(json.dumps(output_data, indent=2))
                                          
    elapsed = time.time() - start_time      
    hash_counts = Counter(manifest.values())             
    dupes = sum(1 for c in hash_counts.values() if c > 1)

    print(f"\n--- Manifest Summary ---")
    print(f"Target:     {out_path.absolute()}")     
    print(f"Indexed:    {len(manifest)}")
    print(f"Skipped:    {skipped}")
    print(f"Errors:     {errors}")
    print(f"Dupe groups: {dupes}")      
    print(f"Elapsed:    {elapsed:.2f}s")          
    print(f"Status:     pyeof successful. Quack!")

if __name__ == "__main__":
    main()
