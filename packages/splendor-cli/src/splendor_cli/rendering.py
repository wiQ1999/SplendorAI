from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from splendor_core import GEM_COLORS, Card, GameState, GemColor, Noble, PlayerState

from splendor_cli.colors import COLOR_LETTER, COLOR_NAME, COLOR_STYLE


def render_game(state: GameState) -> RenderableType:
    return Group(
        _render_bank_and_nobles(state),
        _render_visible_cards(state),
        _render_players(state),
    )


def _render_bank_and_nobles(state: GameState) -> RenderableType:
    bank = Text()
    bank.append("Bank:  ")
    for color in (*GEM_COLORS, GemColor.GOLD):
        bank.append(f" {COLOR_LETTER[color]}:", style="")
        bank.append(f"{state.bank.get(color, 0):>2} ", style=COLOR_STYLE[color])

    nobles = Text("\nNobles: ")
    if not state.nobles:
        nobles.append("(none left)", style="dim")
    else:
        for i, n in enumerate(state.nobles):
            nobles.append(_format_noble(n))
            if i < len(state.nobles) - 1:
                nobles.append(" | ")

    return Panel(
        Group(bank, nobles),
        title=f"Turn {state.turn}  —  Player {state.current_player + 1} to move",
        border_style="cyan",
    )


def _format_noble(noble: Noble) -> Text:
    t = Text()
    t.append(f"+{noble.prestige} ", style="bold yellow")
    parts: list[str] = []
    for color, n in noble.requirement.items():
        parts.append(f"{n}{COLOR_LETTER[color]}")
    t.append("(" + " ".join(parts) + ")", style="dim")
    return t


def _render_visible_cards(state: GameState) -> RenderableType:
    table = Table(title="Cards on table", expand=True)
    table.add_column("Tier", justify="center", style="bold")
    for i in range(4):
        table.add_column(f"slot {i}", justify="left")

    for tier in (3, 2, 1):
        row: list[RenderableType] = [Text(f"T{tier}", style="bold")]
        for slot in state.visible[tier]:
            if slot is None:
                row.append(Text("—", style="dim"))
            else:
                row.append(_format_card(slot))
        table.add_row(*row)
    return table


def _format_card(card: Card) -> Text:
    t = Text()
    t.append(f"+{card.prestige} ", style="bold yellow")
    t.append(f"[{COLOR_LETTER[card.bonus]}]", style=COLOR_STYLE[card.bonus])
    t.append("\n")
    parts: list[Text] = []
    for color, n in card.cost.items():
        if n <= 0:
            continue
        p = Text()
        p.append(f"{n}", style="")
        p.append(COLOR_LETTER[color], style=COLOR_STYLE[color])
        parts.append(p)
    for i, p in enumerate(parts):
        if i:
            t.append(" ")
        t.append_text(p)
    return t


def _render_players(state: GameState) -> RenderableType:
    table = Table(title="Players", expand=True)
    table.add_column("#", justify="center")
    table.add_column("Prestige", justify="right", style="bold yellow")
    table.add_column("Tokens")
    table.add_column("Bonuses")
    table.add_column("Reserved", justify="center")
    table.add_column("Nobles", justify="center")

    for i, p in enumerate(state.players):
        marker = "▶ " if i == state.current_player else "  "
        header = Text(
            f"{marker}P{i + 1}", style="bold cyan" if i == state.current_player else ""
        )
        table.add_row(
            header,
            str(p.prestige),
            _tokens_text(p.tokens),
            _tokens_text(p.bonuses),
            str(len(p.reserved)),
            str(len(p.nobles)),
        )
    return table


def _tokens_text(tokens: dict[GemColor, int]) -> Text:
    t = Text()
    first = True
    for color in (*GEM_COLORS, GemColor.GOLD):
        n = tokens.get(color, 0)
        if n <= 0:
            continue
        if not first:
            t.append(" ")
        first = False
        t.append(f"{n}", style="")
        t.append(COLOR_LETTER[color], style=COLOR_STYLE[color])
    if first:
        t.append("—", style="dim")
    return t


def render_current_player(state: GameState) -> RenderableType:
    player = state.players[state.current_player]
    title = (
        f"Current player — P{state.current_player + 1}  (prestige {player.prestige})"
    )

    body = Group(
        _labeled("Tokens", _tokens_text(player.tokens)),
        _labeled("Bonuses", _tokens_text(player.bonuses)),
        _reserved_table(player),
        _purchased_summary(player),
        _owned_nobles(player),
    )
    return Panel(body, title=title, border_style="green")


def _labeled(label: str, renderable: RenderableType) -> Text:
    t = Text()
    t.append(f"{label}: ", style="bold")
    if isinstance(renderable, Text):
        t.append_text(renderable)
    else:
        t.append(str(renderable))
    return t


def _reserved_table(player: PlayerState) -> RenderableType:
    if not player.reserved:
        return Text("Reserved: (none)", style="dim")
    t = Text("Reserved:\n", style="bold")
    for i, card in enumerate(player.reserved):
        t.append(f"  r{i}: ")
        t.append_text(_format_card(card))
        t.append("\n")
    return t


def _purchased_summary(player: PlayerState) -> Text:
    counts: dict[GemColor, int] = {}
    for card in player.purchased:
        counts[card.bonus] = counts.get(card.bonus, 0) + 1
    t = Text("Purchased: ", style="bold")
    if not counts:
        t.append("(none)", style="dim")
        return t
    first = True
    for color in GEM_COLORS:
        n = counts.get(color, 0)
        if n <= 0:
            continue
        if not first:
            t.append(" ")
        first = False
        t.append(f"{n}×", style="")
        t.append(COLOR_NAME[color], style=COLOR_STYLE[color])
    return t


def _owned_nobles(player: PlayerState) -> Text:
    t = Text("Nobles: ", style="bold")
    if not player.nobles:
        t.append("(none)", style="dim")
        return t
    for i, n in enumerate(player.nobles):
        if i:
            t.append(", ")
        t.append_text(_format_noble(n))
    return t
