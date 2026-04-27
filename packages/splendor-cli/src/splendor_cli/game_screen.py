from __future__ import annotations

from typing import cast

from rich.console import Group
from rich.text import Text
from splendor_core import GamePhase, GameState, apply_action, new_game, returns
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from splendor_cli.commands import (
    CommandError,
    build_suggestions,
    parse_command,
)
from splendor_cli.rendering import render_current_player, render_game


class GameScreen(Screen[None]):
    BINDINGS = [Binding("escape", "app.pop_screen", "Menu")]

    CSS = """
    #board { height: 1fr; }
    #suggestions {
        height: auto;
        max-height: 14;
        border-top: heavy $primary;
        padding: 0 1;
        background: $panel;
    }
    #suggestions-title {
        color: $accent;
        text-style: bold;
    }
    #prompt {
        height: 3;
        border: heavy $accent;
    }
    #error {
        height: 1;
        padding: 0 1;
        color: $error;
    }
    #status {
        height: 1;
        padding: 0 1;
        color: $success;
    }
    """

    def __init__(self, num_players: int) -> None:
        super().__init__()
        self._state: GameState = new_game(num_players)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=False)
        with Vertical():
            with VerticalScroll(id="board"):
                yield Static(id="board-view")
            yield Static(id="suggestions")
            yield Input(
                placeholder="Type a command: take | buy | reserve | exit",
                id="prompt",
            )
            yield Static("", id="error")
            yield Static("", id="status")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_board()
        self._refresh_suggestions("")
        self.query_one("#prompt", Input).focus()

    # -------------------- events --------------------

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "prompt":
            return
        self._clear_error()
        self._refresh_suggestions(event.value)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "prompt":
            return
        raw = event.value
        event.input.value = ""
        if not raw.strip():
            return
        self._handle_submit(raw)

    # -------------------- logic --------------------

    def _handle_submit(self, raw: str) -> None:
        try:
            parsed = parse_command(raw, self._state)
        except CommandError as exc:
            self._set_error(str(exc))
            return

        if parsed.exit:
            cast(App[None], getattr(self, "app")).pop_screen()  # noqa: B009
            return

        assert parsed.action is not None
        try:
            apply_action(self._state, parsed.action)
        except Exception as exc:
            self._set_error(f"Engine rejected action: {exc}")
            return

        self._set_status(f"Applied: {_action_label(parsed.action)}")
        self._refresh_board()
        self._refresh_suggestions("")

        if self._state.phase == GamePhase.FINISHED:
            self._show_game_over()

    def _refresh_board(self) -> None:
        view = self.query_one("#board-view", Static)
        view.update(
            Group(
                render_game(self._state),
                render_current_player(self._state),
            )
        )

    def _refresh_suggestions(self, raw: str) -> None:
        widget = self.query_one("#suggestions", Static)
        if self._state.phase == GamePhase.FINISHED:
            widget.update(Text("(game finished — press Esc for menu)", style="dim"))
            return

        suggestions = build_suggestions(raw, self._state)
        title = Text("Suggestions:", style="bold cyan")
        if not suggestions:
            widget.update(
                Group(
                    title,
                    Text("  (no matches — press Esc to return to menu)", style="dim"),
                )
            )
            return

        lines: list[Text] = [title]
        for s in suggestions:
            line = Text("  ")
            line.append_text(s.text)
            lines.append(line)
        widget.update(Group(*lines))

    def _set_error(self, message: str) -> None:
        self.query_one("#error", Static).update(Text(f"✖ {message}", style="bold red"))
        self.query_one("#status", Static).update("")

    def _clear_error(self) -> None:
        self.query_one("#error", Static).update("")

    def _set_status(self, message: str) -> None:
        self.query_one("#status", Static).update(Text(message, style="green"))
        self._clear_error()

    def _show_game_over(self) -> None:
        scores = returns(self._state)
        winner_indexes = [i for i, r in enumerate(scores) if r > 0]
        standings = ", ".join(
            f"P{i + 1}: {p.prestige}" for i, p in enumerate(self._state.players)
        )
        if len(winner_indexes) == 1:
            headline = f"Game over — P{winner_indexes[0] + 1} wins! ({standings})"
        else:
            tied = "/".join(f"P{i + 1}" for i in winner_indexes)
            headline = f"Game over — tie between {tied}. ({standings})"
        self._set_status(headline)


def _action_label(action: object) -> str:
    from splendor_core import Buy, Reserve, TakeThree, TakeTwo

    if isinstance(action, TakeThree):
        names = ", ".join(c.value for c in action.colors)
        return f"take three ({names})"
    if isinstance(action, TakeTwo):
        return f"take two {action.color.value}"
    if isinstance(action, Reserve):
        spot = "blind" if action.index is None else f"slot {action.index}"
        return f"reserve t{action.tier} {spot}"
    if isinstance(action, Buy):
        if action.source == "reserve":
            return f"buy reserved r{action.index}"
        return f"buy t{action.tier} slot {action.index}"
    return "unknown action"
