#!/usr/bin/env python3
"""Minimal Textual TUI shell for ez_jukebox, bound to real mpc commands."""
from __future__ import annotations

import subprocess

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Footer, Header, Input, Label, ListItem, ListView, Static

from thefuzz import process

MPC = "mpc"


def mpc_current() -> str:
    try:
        result = subprocess.run(
            [MPC, "current"], capture_output=True, text=True, timeout=2
        )
        return result.stdout.strip() or "Nothing playing"
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return f"mpc error: {exc}"


def mpc_playlist_map() -> dict[int, str]:
    """Fresh read of the current queue every call - deliberately no caching.

    mpc queue positions are 1-indexed and match the line order of
    `mpc playlist`, so `mpc play <position>` stays correct even if a
    background watcher refills the queue between keystrokes.
    """
    try:
        result = subprocess.run(
            [MPC, "playlist"], capture_output=True, text=True, timeout=2
        )
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        return {i: line for i, line in enumerate(lines, start=1)}
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}


class JukeboxTUI(App):
    """Minimal MPD-bound TUI shell: play/pause, next, prev, fuzzy search."""

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
    #search {
        display: none;
        margin: 1 2;
    }
    #search.visible {
        display: block;
    }
    #results {
        display: none;
        height: 12;
        margin: 0 2;
    }
    #results.visible {
        display: block;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("space", "play_pause", "Play/Pause"),
        Binding("n", "next", "Next"),
        Binding("p", "prev", "Prev"),
        Binding("slash", "focus_search", "Search", key_display="/"),
        Binding("escape", "clear_search", "Clear search", show=False),
    ]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Parallel to #results contents: list index -> real queue position.
        # Rebuilt from scratch alongside every fresh mpc read, never cached,
        # so a selection always maps back to a position mpc still recognizes.
        self.filtered_positions: list[int] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(mpc_current(), id="now-playing")
        yield Horizontal(
            Button("Prev", id="prev"),
            Button("Play/Pause", id="play-pause", variant="primary"),
            Button("Next", id="next"),
            id="controls",
        )
        yield Input(placeholder="Search queue... (Enter plays top match)", id="search")
        yield ListView(id="results")
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

    # ----- Fuzzy search --------------------------------------------------

    def action_focus_search(self) -> None:
        search = self.query_one("#search", Input)
        search.add_class("visible")
        self.query_one("#results", ListView).add_class("visible")
        search.focus()

    def action_clear_search(self) -> None:
        search = self.query_one("#search", Input)
        search.value = ""
        search.remove_class("visible")
        results = self.query_one("#results", ListView)
        results.remove_class("visible")
        results.clear()
        self.filtered_positions = []
        self.set_focus(None)

    async def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "search":
            return
        await self._apply_search(event.value)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "search" or not self.filtered_positions:
            return
        position = self.filtered_positions[0]
        subprocess.run([MPC, "play", str(position)], check=False)
        self._refresh_now_playing()
        self.action_clear_search()

    async def _apply_search(self, query: str) -> None:
        results = self.query_one("#results", ListView)
        results.clear()
        self.filtered_positions = []

        if not query.strip():
            return

        # Fresh fetch on every keystroke - no caching, so a background
        # watcher refilling the queue never leaves us with stale results.
        playlist_map = mpc_playlist_map()
        if not playlist_map:
            return

        for track_str, _score, position in process.extract(query, playlist_map, limit=15):
            await results.append(ListItem(Label(track_str)))
            self.filtered_positions.append(position)

    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.list_view.id != "results":
            return
        index = event.list_view.index
        if index is None or index >= len(self.filtered_positions):
            return
        position = self.filtered_positions[index]
        subprocess.run([MPC, "play", str(position)], check=False)
        self._refresh_now_playing()
        self.action_clear_search()


if __name__ == "__main__":
    JukeboxTUI().run()
