#!/usr/bin/env python3
# ==============================================================================
# ez_jukebox - Library Integrity Check
# ==============================================================================
import json
import os
from pathlib import Path

def audit_library(manifest_path, library_root):
    if not os.path.exists(manifest_path):
        print(f"[-] Manifest not found at {manifest_path}")
        return [], []
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    missing, orphans = [], []
    for entry in manifest:
        file_path = Path(library_root) / entry['relative_path']
        if not file_path.exists():
            missing.append(entry['relative_path'])
            
    for root, _, files in os.walk(library_root):
        for file in files:
            rel_path = Path(root).relative_to(library_root) / file
            if not any(e['relative_path'] == str(rel_path) for e in manifest):
                orphans.append(rel_path)
    return missing, orphans

if __name__ == "__main__":
    m_path = "music_manifest.json"
    l_root = os.path.expanduser("~/Music-library")
    miss, orph = audit_library(m_path, l_root)
    print(f"\n--- Library Audit ---\n❌ Missing: {len(miss)}\n👻 Orphans: {len(orph)}\n--------------------")
