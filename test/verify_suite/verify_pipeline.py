#!/usr/bin/env python3
"""
ez_jukebox Pipeline Verification Suite
Automated checks between processing stages
"""

import os
import sys
import json
import subprocess
from pathlib import Path

class VerificationSuite:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.manifest_path = self.project_root / "music_manifest.json"
        self.media_path = Path("/mnt/chromeos/removable/CarterMedia")
        self.errors = []

    def check_manifest_integrity(self):
        """Verify manifest structure and content"""
        print("\n🔍 Checking manifest integrity...")

        if not self.manifest_path.exists():
            self.errors.append(f"music_manifest.json not found at {self.manifest_path}")
            return False

        try:
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)

            if not isinstance(manifest, dict):
                self.errors.append("Manifest is not a dictionary")
                return False

            if "_metadata" in manifest:
                print(f"  ℹ️  Manifest Format: {manifest['_metadata'].get('format', 'unknown')}")

            total_entries = sum(1 for k in manifest if k != "_metadata")
            print(f"  ✅ Manifest contains {total_entries:,} indexed items")
            return True

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON: {str(e)}")
            return False

    def check_media_path(self):
        """Verify media path accessibility"""
        print("\n🔍 Checking media path...")

        if not self.media_path.exists():
            self.errors.append(f"Media path not found: {self.media_path}")
            return False

        if not os.access(self.media_path, os.R_OK):
            self.errors.append(f"Insufficient read permissions for {self.media_path}")
            return False

        print(f"  ✅ Media path accessible: {self.media_path}")
        return True

    def check_disk_space(self):
        """Verify sufficient disk space"""
        print("\n🔍 Checking disk space...")

        if not self.media_path.exists():
            self.errors.append("Cannot check disk space: Media path unavailable")
            return False

        try:
            stat = os.statvfs(self.media_path)
            free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024 ** 3)

            if free_space_gb < 1.0:
                self.errors.append(f"Low disk space: {free_space_gb:.2f} GB remaining")
                return False

            print(f"  ✅ Sufficient disk space: {free_space_gb:.2f} GB free")
            return True
        except Exception as e:
            self.errors.append(f"Could not check disk space: {str(e)}")
            return False

    def check_mpd_status(self):
        """Verify MPD is running"""
        print("\n🔍 Checking MPD status...")

        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "mpd"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip() != "active":
                print("  ⚠️ MPD user service is not active (non-fatal)")
                return True
            print("  ✅ MPD user service is active")
            return True
        except Exception:
            print("  ⚠️ Systemctl unavailable or MPD not set up as user service (non-fatal)")
            return True

    def run_all_checks(self):
        """Execute all verification checks"""
        print("\n" + "="*50)
        print("🦆 ez_jukebox Verification Suite")
        print("="*50)

        checks = [
            self.check_manifest_integrity,
            self.check_media_path,
            self.check_disk_space,
            self.check_mpd_status
        ]

        results = [check() for check in checks]

        print("\n" + "="*50)
        if all(results) and not self.errors:
            print("✅ All checks passed!")
            return 0
        else:
            print("❌ Verification failed:")
            for error in self.errors:
                print(f"  - {error}")
            return 1

if __name__ == "__main__":
    suite = VerificationSuite()
    sys.exit(suite.run_all_checks())
