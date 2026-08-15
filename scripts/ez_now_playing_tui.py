#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
import urllib.request

ANSI_REGEX = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def visible_len(s: str) -> int:
    return len(ANSI_REGEX.sub('', s))

def pad_box_line(content: str, width: int) -> str:
    v_len = visible_len(content)
    padding = max(0, width - v_len)
    return content + (" " * padding)

def fetch_now_playing(url: str) -> dict | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ez_jukebox_tui/1.0"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None

def render_tui(data: dict | None, url: str) -> str:
    box_width = 56
    inner_width = box_width - 4

    # Colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"

    def trunc(text: str, max_len: int) -> str:
        return text if len(text) <= max_len else text[: max_len - 3] + "..."

    lines = []

    if not data:
        header_status = f"{RED}● OFFLINE{RESET}"
        body = [
            f"{RED}⚠️  Unable to connect to API{RESET}",
            f"{DIM}URL: {url}{RESET}",
            f"{DIM}Waiting for ez-jukebox-now-playing-api...{RESET}"
        ]
    else:
        state = str(data.get("state", "UNKNOWN")).upper()
        state_color = GREEN if state == "PLAYING" else YELLOW
        header_status = f"{state_color}● {state}{RESET}"

        title = trunc(str(data.get("title", "Unknown Track")), inner_width - 9)
        artist = trunc(str(data.get("artist", "Unknown Artist")), inner_width - 10)
        album = trunc(str(data.get("album", "Unknown Album")), inner_width - 9)
        shuffle = str(data.get("shuffle", "OFF")).upper()
        updated_at = str(data.get("updated_at", ""))

        body = [
            f"{BOLD}{CYAN}🎵 Track  :{RESET} {title}",
            f"{BOLD}{YELLOW}👤 Artist :{RESET} {artist}",
            f"{BOLD}{MAGENTA}💿 Album  :{RESET} {album}",
            f"{DIM}🔀 Shuffle: {shuffle}  |  Updated: {updated_at}{RESET}"
        ]

    header_left = f"{BOLD}📻 ez_jukebox TUI{RESET}"
    header_str = f"{header_left}  [{header_status}]"

    lines.append(f"┌{'─' * (box_width - 2)}┐")
    lines.append(f"│ {pad_box_line(header_str, inner_width)} │")
    lines.append(f"├{'─' * (box_width - 2)}┤")
    for b in body:
        lines.append(f"│ {pad_box_line(b, inner_width)} │")
    lines.append(f"└{'─' * (box_width - 2)}┘")

    return "\n".join(lines)

def main() -> None:
    parser = argparse.ArgumentParser(description="Live TUI widget for ez_jukebox API")
    parser.add_argument("--url", default="http://127.0.0.1:8765/now_playing.json", help="API URL")
    parser.add_argument("--interval", type=float, default=1.0, help="Refresh interval in seconds")
    args = parser.parse_args()

    # Clear screen and hide cursor
    sys.stdout.write("\033[?25l\033[2J")
    sys.stdout.flush()

    try:
        while True:
            data = fetch_now_playing(args.url)
            output = render_tui(data, args.url)

            # Move cursor to top-left and overwrite
            sys.stdout.write("\033[H" + output + "\n")
            sys.stdout.flush()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        # Restore cursor on exit
        sys.stdout.write("\033[?25h\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
