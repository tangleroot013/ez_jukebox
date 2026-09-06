#!/usr/bin/env python3
"""Minimal Textual TUI shell for ez_jukebox, bound to real mpc commands."""
from __future__ import annotations

import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Static

MPC = "mpc"


def mpc_current() -> str:
    try:
        result = subprocess.run(
            [MPC, "current"], capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() or "Nothing playing"
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return f"mpc error: {exc}"


class JukeboxTUI(App):
    """Minimal MPD-bound TUI shell: play/pause, next, prev."""

    CSS = """
    Screen {
        align: center middle;
    }
    #now-playing {
        width: 100%;
        content-align: center middle;
        padding: 1;
    }
    #controls {
        align: center middle;
        height: auto;
    }
    Button {
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("space", "play_pause", "Play/Pause"),
        Binding("n", "next", "Next"),
        Binding("p", "prev", "Prev"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(mpc_current(), id="now-playing")
        yield Horizontal(
            Button("Prev", id="prev"),
            Button("Play/Pause", id="play-pause", variant="primary"),
            Button("Next", id="next"),
            id="controls",
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        {
            "prev": self.action_prev,
            "play-pause": self.action_play_pause,
            "next": self.action_next,
        }[event.button.id]()

    def _refresh_now_playing(self) -> None:
        self.query_one("#now-playing", Static).update(mpc_current())

    def action_play_pause(self) -> None:
        subprocess.run([MPC, "toggle"], check=False)
        self._refresh_now_playing()

    def action_next(self) -> None:
        subprocess.run([MPC, "next"], check=False)
        self._refresh_now_playing()

    def action_prev(self) -> None:
        subprocess.run([MPC, "prev"], check=False)
        self._refresh_now_playing()


if __name__ == "__main__":
    JukeboxTUI().run()
