#!/usr/bin/env python3
import os, sys, time, json, shutil, subprocess
from datetime import datetime

LIBRARY_PATH = "/mnt/chromeos/removable/CarterMedia"
MANIFEST_PATH = "music_manifest.json"

CLR = {"reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "cyan": "\033[38;5;51m", "green": "\033[38;5;82m", "yellow": "\033[38;5;220m", "magenta": "\033[38;5;201m", "blue": "\033[38;5;39m", "red": "\033[38;5;196m"}

def get_active_processes():
    targets = ["build_manifest.py", "sample_rate_sentinel.py", "dedup_executor.py", "mpd"]
    active = []
    try:
        ps_out = subprocess.check_output(["ps", "aux"], text=True)
        for line in ps_out.splitlines():
            for target in targets:
                if target in line and "monitor_jukebox" not in line and "grep" not in line:
                    parts = line.split(maxsplit=10)
                    active.append((target, parts[1], parts[2], parts[3]))
    except Exception:
        pass
    return active

def render_dashboard():
    print("\033[H\033[J", end="")
    term_width = shutil.get_terminal_size((80, 24)).columns
    print(f"{CLR['cyan']}{CLR['bold']}🎵 ez_jukebox Live Dashboard {CLR['dim']}— Press Ctrl+C to exit{CLR['reset']}")
    print(f"{CLR['dim']}{'━' * term_width}{CLR['reset']}\n")
    
    print(f"{CLR['yellow']}{CLR['bold']}▶ Active Processes{CLR['reset']}")
    procs = get_active_processes()
    if procs:
        for name, pid, cpu, mem in procs:
            print(f"  {CLR['green']}●{CLR['reset']} {CLR['bold']}{name:<22}{CLR['reset']} PID: {CLR['cyan']}{pid:<6}{CLR['reset']} CPU: {CLR['yellow']}{cpu}%{CLR['reset']} MEM: {CLR['magenta']}{mem}%{CLR['reset']}")
    else:
        print(f"  {CLR['dim']}No active audio processing pipeline detected (Idle){CLR['reset']}")

    print(f"\n{CLR['yellow']}{CLR['bold']}▶ Manifest Status{CLR['reset']}")
    if os.path.exists(MANIFEST_PATH):
        size = os.path.getsize(MANIFEST_PATH) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(MANIFEST_PATH)).strftime('%H:%M:%S')
        print(f"  Manifest Size : {CLR['cyan']}{size:.2f} MB{CLR['reset']}")
        print(f"  Last Modified : {CLR['blue']}{mtime}{CLR['reset']}")
    else:
        print(f"  {CLR['red']}Manifest file not found.{CLR['reset']}")
        
    print(f"\n{CLR['dim']}{'━' * term_width}{CLR['reset']}")
    print(f"{CLR['dim']}Last updated: {datetime.now().strftime('%H:%M:%S')} (Auto-refresh 1.5s){CLR['reset']}")

def main():
    try:
        while True:
            render_dashboard()
            time.sleep(1.5)
    except KeyboardInterrupt:
        print(f"\n{CLR['cyan']}Exiting monitor. Have a great session! 🎧{CLR['reset']}")

if __name__ == "__main__":
    main()
