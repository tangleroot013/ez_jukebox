import os
from pathlib import Path

APP_NAME = "ez_jukebox"
BASE_DIR = (
    Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    / APP_NAME
)
CACHE_DIR = BASE_DIR / "cache"
STATE_DIR = BASE_DIR / "state"
QUARANTINE_DIR = BASE_DIR / "quarantine"
REPORTS_DIR = BASE_DIR / "reports"

MANIFEST_PATH = BASE_DIR / "music_manifest.json"
DUPLICATES_PATH = BASE_DIR / "duplicates.txt"
RECOVERY_PATH = STATE_DIR / "recovery_state.json"


def ensure_dirs():
    for p in [BASE_DIR, CACHE_DIR, STATE_DIR, QUARANTINE_DIR, REPORTS_DIR]:
        p.mkdir(parents=True, exist_ok=True)
