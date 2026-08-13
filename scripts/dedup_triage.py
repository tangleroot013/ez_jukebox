#!/usr/bin/env python3
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ez_jukebox.manifest import load_json, save_json
from ez_jukebox.paths import DUPLICATES_PATH, REPORTS_DIR, ensure_dirs

def parse_duplicates(path: Path):
    if not path.exists():
        return []
    groups = []
    current = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            if current:
                groups.append(current)
                current = []
            continue
        current.append(line)
    if current:
        groups.append(current)
    return groups

def render_html(groups):
    rows = []
    for i, group in enumerate(groups, 1):
        items = "".join(f"<li><code>{html.escape(x)}</code></li>" for x in group)
        rows.append(f"<h2>Group {i}</h2><ul>{items}</ul>")
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>Dedup Triage</title></head>
<body>
<h1>Dedup Triage</h1>
{''.join(rows) if rows else '<p>No duplicates found.</p>'}
</body>
</html>"""

def main():
    ensure_dirs()
    groups = parse_duplicates(DUPLICATES_PATH)
    out_html = REPORTS_DIR / "dedup_triage.html"
    out_json = REPORTS_DIR / "dedup_triage.json"

    save_json(out_json, {"groups": groups})
    out_html.write_text(render_html(groups), encoding="utf-8")

    print(f"Wrote {out_html}")
    print(f"Wrote {out_json}")

if __name__ == "__main__":
    main()
