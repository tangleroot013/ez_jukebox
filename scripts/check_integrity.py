#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ez_jukebox.manifest import load_json, save_json
from ez_jukebox.paths import MANIFEST_PATH, REPORTS_DIR, ensure_dirs

def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    ensure_dirs()
    manifest = load_json(MANIFEST_PATH, default={"files": []})
    files = manifest.get("files", [])

    results = []
    for item in files:
        p = Path(item["path"]).expanduser()
        expected = item.get("sha256")
        if not p.exists():
            results.append({"path": str(p), "status": "missing"})
            continue
        actual = sha256_file(p)
        status = "ok" if actual == expected else "mismatch"
        results.append({"path": str(p), "status": status, "expected": expected, "actual": actual})

    out = REPORTS_DIR / "integrity_report.json"
    save_json(out, {"results": results})
    print(f"Wrote {out}")

    bad = [r for r in results if r["status"] != "ok"]
    if bad:
        print("Integrity check failed:")
        for r in bad:
            print(f"- {r['path']}: {r['status']}")
        raise SystemExit(1)

    print("Integrity check passed")

if __name__ == "__main__":
    main()
