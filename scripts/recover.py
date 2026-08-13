#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ez_jukebox.manifest import load_json, save_json
from ez_jukebox.paths import QUARANTINE_DIR, RECOVERY_PATH, ensure_dirs

def restore_quarantine():
    restored = []
    for src in QUARANTINE_DIR.rglob("*"):
        if src.is_file():
            rel = src.relative_to(QUARANTINE_DIR)
            dst = Path.home() / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            restored.append(str(dst))
    return restored

def main():
    ensure_dirs()
    state = load_json(RECOVERY_PATH, default={"runs": []})

    restored = restore_quarantine()
    state["runs"].append({"restored": restored})
    save_json(RECOVERY_PATH, state)

    print("Recovery complete")
    for p in restored:
        print(f"restored: {p}")

if __name__ == "__main__":
    main()
