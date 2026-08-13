#!/usr/bin/env python3
"""dedupe_justfile.py - remove duplicate recipe definitions, keep first occurrence."""
import re, shutil, sys
from pathlib import Path

path = Path(sys.argv[1] if len(sys.argv) > 1 else "justfile")
lines = path.read_text().splitlines(keepends=True)

recipe_re = re.compile(r'^([A-Za-z_][\w-]*)\s*:.*$')

seen = set()
out = []
skipping = False
dropped = []

for line in lines:
    m = recipe_re.match(line) if not line.startswith((' ', '\t')) else None
    if m:
        name = m.group(1)
        if name in seen:
            skipping = True
            dropped.append(name)
            continue
        seen.add(name)
        skipping = False
        out.append(line)
        continue
    if skipping:
        if line.strip() == "" or line.startswith((' ', '\t')):
            continue
        else:
            skipping = False
    out.append(line)

if dropped:
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copy(path, backup)
    path.write_text("".join(out))
    print(f"[ok] removed duplicate recipe(s): {', '.join(sorted(set(dropped)))}")
    print(f"[ok] backup saved to {backup}")
else:
    print("[skip] no duplicate recipes found")
