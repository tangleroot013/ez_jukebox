#!/usr/bin/env python3
"""
ez_jukebox Parallel Deduplication Executor
Executes quarantine moves concurrently using multi-core worker pools.
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

MANIFEST = Path("music_manifest.json")

# Default quarantine directory placed directly on the removable drive to avoid cross-device copies
DEFAULT_LIBRARY = "/mnt/chromeos/removable/CarterMedia"
LIBRARY_ROOT = Path(os.environ.get("LIBRARY_ROOT", DEFAULT_LIBRARY)).resolve()
QUARANTINE = LIBRARY_ROOT / "_dedup_quarantine"
EXECUTE = os.environ.get("EXECUTE", "0") == "1"

def move_single_file(item):
    """Worker task to move one redundant file to quarantine."""
    src_str, rel_path_str = item
    src = Path(src_str)
    dest = QUARANTINE / rel_path_str

    if not src.exists():
        return ("missing", src_str)

    if "_dedup_quarantine" in src.parts:
        return ("already_quarantined", src_str)

    if EXECUTE:
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
            return ("moved", src_str)
        except Exception as e:
            return ("error", f"{src_str}: {e}")
    else:
        return ("planned", src_str)

def main():
    if not MANIFEST.exists():
        print(f"❌ Manifest {MANIFEST} not found.")
        sys.exit(1)

    print("⚡ ez_jukebox High-Speed Parallel Deduplication Executor")
    print(f"  Mode: {'EXECUTE (Moving files)' if EXECUTE else 'DRY-RUN (Preview)'}")
    print(f"  Library Target:    {LIBRARY_ROOT}")
    print(f"  Quarantine Target: {QUARANTINE}")

    # Load manifest
    with open(MANIFEST, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Group files by hash
    groups = defaultdict(list)
    for k, v in data.items():
        if k == "_metadata":
            continue
        if isinstance(v, list):
            groups[k].extend(v)
        else:
            groups[v].append(k)

    # Filter duplicate groups (>1 file)
    dup_groups = {h: paths for h, paths in groups.items() if len(paths) > 1}
    print(f"  Duplicate Groups Found: {len(dup_groups):,}")

    # Build queue of redundant files
    queue = []
    for h, paths in dup_groups.items():
        keeper = min(paths, key=lambda p: (
            "_dedup_quarantine" in p,  # Prefer non-quarantined
            len(p),                    # Prefer shorter paths
            p                          # Alphabetical fallback
        ))
        for p in paths:
            if p != keeper:
                # Compute relative path inside library for quarantine layout
                rel_p = os.path.relpath(p, str(LIBRARY_ROOT)) if p.startswith(str(LIBRARY_ROOT)) else os.path.basename(p)
                queue.append((p, rel_p))

    print(f"  Redundant Files Queued: {len(queue):,}")

    if not queue:
        print("✅ No files need to be moved.")
        return

    workers = os.cpu_count() or 4
    print(f"\n🚀 Processing moves using {workers} parallel process workers...")
    
    start_time = time.time()
    stats = defaultdict(int)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(move_single_file, item) for item in queue]
        for future in as_completed(futures):
            status, detail = future.result()
            stats[status] += 1
            processed = sum(stats.values())
            if processed % 500 == 0 or processed == len(queue):
                rate = processed / (time.time() - start_time) if (time.time() - start_time) > 0 else 0
                print(f"   ✓ Processed {processed:,}/{len(queue):,} files ({rate:.1f} ops/sec)...")

    elapsed = time.time() - start_time
    print(f"\n✅ Deduplication Run Finished in {elapsed:.2f}s!")
    print(f"   Moved: {stats['moved']:,} | Planned: {stats['planned']:,} | Skipped/Missing: {stats['already_quarantined'] + stats['missing']:,} | Errors: {stats['error']:,}")

if __name__ == "__main__":
    main()
