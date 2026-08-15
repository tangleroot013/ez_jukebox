#!/usr/bin/env python3
"""
ez_dedup_policy.py - Evaluates duplicate audio tracks and applies retention policy rules.
Outputs triage recommendations to ~/.local/share/ez_jukebox/reports/dedup_policy.json
"""

import json
import os
from pathlib import Path

DUPLICATES_FILE = "duplicates.txt"
REPORT_DIR = Path.home() / ".local/share/ez_jukebox" / "reports"
REPORT_FILE = REPORT_DIR / "dedup_policy.json"

FORMAT_PRIORITY = {
    ".flac": 100,
    ".wav": 90,
    ".alac": 85,
    ".m4a": 70,
    ".ogg": 60,
    ".mp3": 50,
}

def get_format_score(filepath):
    ext = Path(filepath).suffix.lower()
    return FORMAT_PRIORITY.get(ext, 10)

def evaluate_duplicates():
    if not os.path.exists(DUPLICATES_FILE):
        print(f"[error] Duplicates log '{DUPLICATES_FILE}' not found.")
        return

    groups = []
    current_group = []

    with open(DUPLICATES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                if current_group:
                    groups.append(current_group)
                    current_group = []
            elif not line.startswith("#"):
                current_group.append(line)
        if current_group:
            groups.append(current_group)

    results = []

    for idx, group in enumerate(groups, 1):
        evaluated = []
        for file_path in group:
            p = Path(file_path)
            size = p.stat().st_size if p.exists() else 0
            score = get_format_score(file_path)
            evaluated.append({
                "path": file_path,
                "exists": p.exists(),
                "size_bytes": size,
                "format_score": score
            })

        # Rank by format score desc, then size desc
        evaluated.sort(key=lambda x: (x["format_score"], x["size_bytes"]), reverse=True)

        if evaluated:
            keep = evaluated[0]
            remove = evaluated[1:]
            results.append({
                "group_id": idx,
                "keep": keep["path"],
                "remove": [item["path"] for item in remove]
            })

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "total_duplicate_groups": len(results),
        "policy": "Highest quality format > Largest file size",
        "recommendations": results
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ez_jukebox] Evaluated {len(results)} duplicate group(s).")
    print(f"Policy report generated at: {REPORT_FILE}")

if __name__ == "__main__":
    evaluate_duplicates()
