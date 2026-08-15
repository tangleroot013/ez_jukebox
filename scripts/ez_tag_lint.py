#!/usr/bin/env python3
"""
ez_tag_lint.py - Audits music_manifest.json for missing or incomplete metadata tags.
Outputs results to ~/.local/share/ez_jukebox/reports/tag_lint_report.json
"""

import json
import os
from pathlib import Path

MANIFEST_PATH = "music_manifest.json"
REPORT_DIR = Path.home() / ".local/share/ez_jukebox" / "reports"
REPORT_FILE = REPORT_DIR / "tag_lint_report.json"

def audit_tags():
    if not os.path.exists(MANIFEST_PATH):
        print(f"[error] Manifest file '{MANIFEST_PATH}' not found.")
        return

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    tracks = data if isinstance(data, list) else data.get("tracks", [])
    flagged = []

    for track in tracks:
        file_path = track.get("file") or track.get("path") or "unknown_file"
        issues = []

        if not track.get("artist") or track.get("artist") == "Unknown Artist":
            issues.append("missing_artist")
        if not track.get("title") or track.get("title") == "Unknown Title":
            issues.append("missing_title")
        if not track.get("album") or track.get("album") == "Unknown Album":
            issues.append("missing_album")
        if not track.get("genre"):
            issues.append("missing_genre")

        if issues:
            flagged.append({
                "file": file_path,
                "issues": issues
            })

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "total_tracks_scanned": len(tracks),
        "total_flagged": len(flagged),
        "flagged_tracks": flagged
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"[ez_jukebox] Tag lint complete. {len(flagged)} track(s) flagged out of {len(tracks)} scanned.")
    print(f"Report saved to: {REPORT_FILE}")

if __name__ == "__main__":
    audit_tags()
