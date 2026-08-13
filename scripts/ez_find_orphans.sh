#!/bin/bash
# ez_find_orphans.sh v2.2 - Interactive Wizard to find missing files
set -euo pipefail

# Pass all bash arguments directly to the python script
python3 - "$@" << 'PYEOF'
import sys
import os
import json
import sqlite3
from pathlib import Path

def print_header():
    print("\033[1;36m" + "="*55)
    print(" 🕵️‍♂️  ez_jukebox Orphan Finder Wizard v2.2")
    print("="*55 + "\033[0m")
    print("Comparing your library index against the actual disk\n")

def get_target():
    # If the user passed a file argument, skip the wizard
    if len(sys.argv) > 1:
        return sys.argv[1]
        
    print("Please choose a library file to check:")
    candidates = ["music_manifest.json", "ez_test_env/jukebox.db", "jukebox.db"]
    found = [c for c in candidates if os.path.exists(c)]
    options = found + ["Type a custom path..."]
    
    for i, opt in enumerate(options):
        print(f"  \033[1;33m{i+1})\033[0m {opt}")
        
    while True:
        try:
            choice = input("\n👉 Enter your choice (1-" + str(len(options)) + "): ")
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                if options[idx] == "Type a custom path...":
                    return input("   Enter the exact path: ")
                return options[idx]
            print("❌ Invalid choice. Try again.")
        except (ValueError, KeyboardInterrupt):
            print("\n🚪 Exiting wizard. Quack!")
            sys.exit(0)

def main():
    if len(sys.argv) <= 1:
        print_header()
        
    target = get_target()
    if not os.path.exists(target):
        print(f"\n❌ Target not found: '{target}'")
        sys.exit(1)

    files_to_check = []
    print(f"\n\033[1;34m[*] Loading library:\033[0m {target}")

    if target.endswith(".json"):
        try:
            data = json.loads(Path(target).read_text())
            # Handle v2.x nested schema or older flat schema
            files_to_check = list(data.get("files", data).keys())
            print(f"  └─ JSON Manifest format ({len(files_to_check)} tracks)")
        except Exception as e:
            print(f"❌ JSON Error: {e}")
            sys.exit(1)
    else:
        try:
            conn = sqlite3.connect(target)
            cur = conn.cursor()
            # Verify table existence to avoid crashes
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_fingerprints'")
            if not cur.fetchone():
                print("❌ Table 'audio_fingerprints' not found in database.")
                sys.exit(1)
            cur.execute("SELECT filepath FROM audio_fingerprints")
            files_to_check = [row[0] for row in cur.fetchall()]
            print(f"  └─ SQLite Database format ({len(files_to_check)} tracks)")
        except Exception as e:
            print(f"❌ DB Error: {e}")
            sys.exit(1)

    total = len(files_to_check)
    if total == 0:
        print("\n⚠️  Library is empty!")
        sys.exit(0)
        
    print(f"🔍 Scanning disk... (this may take a moment on removable drives)\n")

    orphans = []
    for i, filepath in enumerate(files_to_check, 1):
        # Progress bar every 100 files
        if i % 100 == 0 or i == total:
            sys.stdout.write(f"\r   Progress: {i}/{total} files checked...")
            sys.stdout.flush()
            
        if not os.path.exists(filepath):
            orphans.append(filepath)

    print("\n\n\033[1;36m" + "-"*55 + "\033[0m")
    if not orphans:
        print(f"✅ \033[1;32mLibrary health is perfect!\033[0m All {total} files exist.")
    else:
        print(f"⚠️  \033[1;31mFound {len(orphans)} orphaned entries\033[0m (out of {total}).")
        
        print(f"\n   Preview (first 5):")
        for mp in orphans[:5]:
            print(f"    - {mp}")
        
        export_file = "orphans_list.txt"
        try:
            with open(export_file, "w") as f:
                f.write("\n".join(orphans))
            print(f"\n📝 Full list saved to: \033[1;33m{export_file}\033[0m")
        except Exception as e:
            print(f"⚠️  Could not write export file: {e}")
            
        print("\n💡 \033[1mRecommended Action:\033[0m")
        if target.endswith(".json"):
            print("   Run `python3 scripts/rebuild_manifest.py` to refresh your JSON manifest.")
        else:
            print("   Trigger an MPD/Jukebox library rescan to clean up database ghosts.")
    print("\033[1;36m" + "-"*55 + "\033[0m")

if __name__ == "__main__":
    main()
PYEOF
