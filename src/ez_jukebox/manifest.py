import json
import os
import tempfile
from pathlib import Path


def load_json(path: Path, default=None):
    if not path.exists():
        return default if default is not None else {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, data):
    from ez_jukebox.atomic_io import atomic_write_json
    atomic_write_json(path, data)
