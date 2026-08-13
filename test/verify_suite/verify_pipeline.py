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
        self.project_root = Path(__file__).parent.parent
        self.manifest_path = self.project_root / "music_manifest.json"
        self.media_path = Path("/mnt/chromeos/removable/CarterMedia")
        self.errors = []

    def check_manifest_integrity(self):
        """Verify manifest structure and content"""
        print("\n🔍 Checking manifest integrity...")

        if not self.manifest_path.exists():
            self.errors.append("music_manifest.json not found")
            return False

        try:
            with open(self.manifest_path) as f:
                manifest = json.load(f)

            if not isinstance(manifest, dict):
                self.errors.append("Manifest is not a dictionary")
                return False

            if "project_metadata" not in manifest:
                self.errors.append("Missing project_metadata")
                return False

            total_files = sum(len(files) for files in manifest.values()
                            if isinstance(files, list) and files)
            print(f"✅ Manifest contains {total_files} indexed files")
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

        if not os.access(self.media_path, os.R_OK | os.W_OK):
            self.errors.append(f"Insufficient permissions for {self.media_path}")
            return False

        print(f"✅ Media path accessible: {self.media_path}")
        return True

    def check_disk_space(self):
        """Verify sufficient disk space"""
        print("\n🔍 Checking disk space...")

        stat = os.statvfs(self.media_path)
        free_space = stat.f_frsize * stat.f_bavail / (1024 ** 3)

        if free_space < 1.0:
            self.errors.append(f"Low disk space: {free_space:.2f}GB remaining")
            return False

        print(f"✅ Sufficient disk space: {free_space:.2f}GB free")
        return True

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
                self.errors.append("MPD is not running")
                return False
            print("✅ MPD is running")
            return True
        except Exception as e:
            self.errors.append(f"MPD check failed: {str(e)}")
            return False

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

        results = []
        for check in checks:
            results.append(check())

        print("\n" + "="*50)
        if all(results):
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
