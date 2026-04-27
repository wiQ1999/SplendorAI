from __future__ import annotations

from typing import cast

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label

from splendor_cli.game_screen import GameScreen


def _app(screen: Screen[None]) -> SplendorApp:
    return cast("SplendorApp", getattr(screen, "app"))  # noqa: B009


class MenuScreen(Screen[None]):
    BINDINGS = [Binding("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Middle():
            with Center():
                yield Label("[b]Splendor CLI[/b]\n", id="title")
            with Center():
                yield Button("Start game", id="start", variant="primary")
            with Center():
                yield Button("Exit", id="exit")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            _app(self).push_screen(SetupScreen())
        elif event.button.id == "exit":
            _app(self).exit()


class SetupScreen(Screen[None]):
    BINDINGS = [Binding("escape", "app.pop_screen", "Back")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Middle():
            with Center():
                yield Label("How many players?\n", id="setup-title")
            with Center():
                with Vertical(id="player-count-col"):
                    yield Button("2 players", id="p2")
                    yield Button("3 players", id="p3")
                    yield Button("4 players", id="p4")
                    yield Button("Back", id="back", variant="warning")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("p") and bid[1:].isdigit():
            n = int(bid[1:])
            _app(self).push_screen(GameScreen(num_players=n))
        elif bid == "back":
            _app(self).pop_screen()


class SplendorApp(App[None]):
    CSS = """
    Screen {
        align: center middle;
    }
    #title {
        content-align: center middle;
        color: $accent;
    }
    #setup-title {
        content-align: center middle;
    }
    Button {
        margin: 1 2;
        min-width: 20;
    }
    #player-count-col {
        width: auto;
        height: auto;
    }
    """

    BINDINGS = [Binding("ctrl+c", "quit", "Quit", show=False)]

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())
