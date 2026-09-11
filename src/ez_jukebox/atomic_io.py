"""Atomic JSON/text write helpers - crash-safe writes for ez_jukebox.

A process killed mid-write (kill -9, power loss, OOM) never leaves a
truncated or corrupted file: write to a temp file in the same directory,
fsync it, then os.replace() -- atomic on POSIX same-filesystem renames.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def atomic_write_text(path, text, encoding="utf-8"):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def atomic_write_json(path, data, *, indent=2, sort_keys=True):
    atomic_write_text(path, json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False))
