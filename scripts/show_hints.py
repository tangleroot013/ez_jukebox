#!/usr/bin/env python3
"""
ez_jukebox - Interactive Startup Hint Banner
Renders a formatted command reference card adapted to current terminal dimensions.
"""

import shutil
import sys

# Standard ANSI Color Escapes
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
DIM = "\033[2m"
RESET = "\033[0m"

def render_banner():
    # Detect terminal width with fallback
    cols, _ = shutil.get_terminal_size(fallback=(80, 24))
    box_width = max(min(cols - 4, 76), 56)

    title = "🎵 ez_jukebox Quick-Start Command Reference"
    
    top_line = f"┌{'─' * (box_width + 2)}┐"
    padded_title = title.ljust(box_width)
    title_line = f"│ {BOLD}{padded_title}{RESET}{CYAN} │"
    bot_line = f"└{'─' * (box_width + 2)}┘"

    divider = f"{DIM}{'─' * (box_width + 4)}{RESET}"

    banner = f"""{CYAN}{top_line}
{title_line}
{bot_line}{RESET}

 {YELLOW}{BOLD}[ Playback Controls ]{RESET}
   • {BOLD}mpc play{RESET} / {BOLD}mpc pause{RESET}        Toggle playback state
   • {BOLD}mpc next{RESET} / {BOLD}mpc prev{RESET}         Skip forward / backward in current queue
   • {BOLD}mpc status{RESET}                  Display playing track info & playback state
   • {BOLD}mpc volume [±N]{RESET}             Adjust volume output level (e.g., `mpc volume +5`)

 {GREEN}{BOLD}[ Queue & Library Search ]{RESET}
   • {BOLD}mpc playlist{RESET}                Display current active playback queue
   • {BOLD}mpc clear{RESET}                   Flush all entries from active playback queue
   • {BOLD}mpc search artist "<Name>"{RESET}   Search indexed music collection by artist
   • {BOLD}mpc add <Path/URI>{RESET}           Enqueue song or folder into active queue

 {MAGENTA}{BOLD}[ System & Maintenance ]{RESET}
   • {BOLD}mpc update{RESET}                  Trigger MPD background library rescan
   • {BOLD}mpc stats{RESET}                   Display library metrics (track count, artists, uptime)
   • {BOLD}just verify{RESET}                 Run automated test & integrity suite
   • {BOLD}python3 scripts/dedup_fast.py{RESET} Run duplicate track finder and manager

{divider}"""
    print(banner)

if __name__ == "__main__":
    render_banner()
