#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ez_jukebox.manifest import load_json, save_json  # noqa: E402
from ez_jukebox.paths import (  # noqa: E402
    MANIFEST_PATH,
    REPORTS_DIR,
    ensure_dirs,
)

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def make_result(path: Path, status: str, **extra: Any) -> dict[str, Any]:
    return {"path": str(path), "status": status, **extra}


def main() -> int:
    ensure_dirs()
    if not MANIFEST_PATH.is_file():
        print(
            f"Integrity check failed: manifest not found at {MANIFEST_PATH}",
            file=sys.stderr,
        )
        return 1

    try:
        manifest = load_json(MANIFEST_PATH)
    except (OSError, ValueError) as exc:
        print(
            f"Integrity check failed: could not read manifest: {exc}",
            file=sys.stderr,
        )
        return 1

    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        print(
            "Integrity check failed: invalid manifest schema at "
            f"{MANIFEST_PATH}",
            file=sys.stderr,
        )
        return 1

    results: list[dict[str, Any]] = []
    for raw_path, expected in files.items():
        path = Path(str(raw_path)).expanduser()
        if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
            results.append(
                make_result(path, "invalid_manifest_hash", expected=expected)
            )
            continue

        if not path.is_file():
            status = "missing" if not path.exists() else "not_a_file"
            results.append(make_result(path, status, expected=expected))
            continue

        try:
            actual = sha256_file(path)
        except OSError as exc:
            results.append(
                make_result(
                    path,
                    "unreadable",
                    expected=expected,
                    error=str(exc),
                )
            )
            continue

        status = "ok" if actual.lower() == expected.lower() else "mismatch"
        results.append(
            make_result(path, status, expected=expected, actual=actual)
        )

    report_path = REPORTS_DIR / "integrity_report.json"
    try:
        save_json(report_path, {"results": results})
    except OSError as exc:
        print(
            f"Integrity check failed: could not write report: {exc}",
            file=sys.stderr,
        )
        return 1
    print(f"Wrote {report_path}")

    failures = [entry for entry in results if entry["status"] != "ok"]
    if failures:
        print("Integrity check failed:")
        for entry in failures:
            print(f"- {entry['path']}: {entry['status']}")
        return 1

    print(f"Integrity check passed: {len(results)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
