from __future__ import annotations

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from splendor_core import GEM_COLORS, Card, GameState, GemColor, Noble, PlayerState

from splendor_cli.colors import COLOR_LETTER, COLOR_STYLE, TAKE_ORDER

# ---------------------------------------------------------------------------
# Format helpers — fixed-width, colored tokens with dashes for zero values.
# ---------------------------------------------------------------------------

DASH_STYLE = "grey39"
PRESTIGE_STYLE = "bold yellow"


def format_cost(cost: dict[GemColor, int]) -> Text:
    """`DSERO` (5 chars). Each digit colored; '-' for zero."""
    t = Text()
    for color in TAKE_ORDER:
        n = cost.get(color, 0)
        if n == 0:
            t.append("-", style=DASH_STYLE)
        else:
            t.append(str(n), style=COLOR_STYLE[color])
    return t


def format_player_tokens(tokens: dict[GemColor, int]) -> Text:
    """`DSEROG` (6 chars). Colored digits, '-' for zero, includes gold."""
    t = format_cost(tokens)
    g = tokens.get(GemColor.GOLD, 0)
    if g == 0:
        t.append("-", style=DASH_STYLE)
    else:
        t.append(str(g), style=COLOR_STYLE[GemColor.GOLD])
    return t


def format_prestige(value: int) -> Text:
    """`+N` (2 chars). `+-` if zero."""
    t = Text()
    if value == 0:
        t.append("+-", style=DASH_STYLE)
    else:
        t.append(f"+{value}", style=PRESTIGE_STYLE)
    return t


def format_bonus(color: GemColor) -> Text:
    """`[X]` (3 chars), letter colored to match the gem."""
    t = Text("[", style=DASH_STYLE)
    t.append(COLOR_LETTER[color], style=COLOR_STYLE[color])
    t.append("]", style=DASH_STYLE)
    return t


def format_card(card: Card) -> Text:
    """`+P [B] DSERO` (12 chars)."""
    t = format_prestige(card.prestige)
    t.append(" ")
    t.append_text(format_bonus(card.bonus))
    t.append(" ")
    t.append_text(format_cost(card.cost))
    return t


def format_noble(noble: Noble) -> Text:
    """`+P DSERO` (8 chars)."""
    t = format_prestige(noble.prestige)
    t.append(" ")
    t.append_text(format_cost(noble.requirement))
    return t


# ---------------------------------------------------------------------------
# Top-level renderers
# ---------------------------------------------------------------------------


def render_game(state: GameState) -> RenderableType:
    return Group(
        _render_bank_and_nobles(state),
        _render_visible_cards(state),
        _render_players(state),
    )


def _render_bank_and_nobles(state: GameState) -> RenderableType:
    bank = Text("Bank:   ", style="bold")
    for color in (*GEM_COLORS, GemColor.GOLD):
        bank.append(COLOR_LETTER[color], style=COLOR_STYLE[color])
        bank.append(":", style=DASH_STYLE)
        n = state.bank.get(color, 0)
        bank.append(f"{n} ", style=COLOR_STYLE[color] if n > 0 else DASH_STYLE)
        bank.append(" ")

    nobles = Text("Nobles: ", style="bold")
    if not state.nobles:
        nobles.append("(none left)", style=DASH_STYLE)
    else:
        for i, n in enumerate(state.nobles):
            if i:
                nobles.append("   ")
            nobles.append_text(format_noble(n))

    return Panel(
        Group(bank, nobles),
        title=f"Turn {state.turn}  —  Player {state.current_player + 1} to move",
        border_style="cyan",
    )


def _render_visible_cards(state: GameState) -> RenderableType:
    table = Table(title="Cards on table", expand=False, padding=(0, 2))
    table.add_column("Tier", justify="center", style="bold")
    for i in range(4):
        table.add_column(f"slot {i}", justify="left")

    for tier in (3, 2, 1):
        row: list[RenderableType] = [Text(f"T{tier}", style="bold")]
        for slot in state.visible[tier]:
            if slot is None:
                row.append(Text("    (empty)   ", style=DASH_STYLE))
            else:
                row.append(format_card(slot))
        table.add_row(*row)
    return table


def _render_players(state: GameState) -> RenderableType:
    table = Table(title="Players", expand=False, padding=(0, 2))
    table.add_column("#", justify="center")
    table.add_column("Prestige", justify="right")
    table.add_column("Tokens (DSEROG)", justify="left")
    table.add_column("Bonuses (DSERO)", justify="left")
    table.add_column("Reserved", justify="center")
    table.add_column("Nobles", justify="center")

    for i, p in enumerate(state.players):
        is_current = i == state.current_player
        marker = "▶ " if is_current else "  "
        header = Text(
            f"{marker}P{i + 1}",
            style="bold cyan" if is_current else "",
        )
        table.add_row(
            header,
            format_prestige(p.prestige),
            format_player_tokens(p.tokens),
            format_cost(p.bonuses),
            str(len(p.reserved)),
            str(len(p.nobles)),
        )
    return table


def render_current_player(state: GameState) -> RenderableType:
    player = state.players[state.current_player]
    title = (
        f"Current player — P{state.current_player + 1}  "
        f"(prestige {player.prestige},  cards owned: {len(player.purchased)})"
    )

    lines: list[Text] = []

    tokens_line = Text("Tokens   (DSEROG):  ", style="bold")
    tokens_line.append_text(format_player_tokens(player.tokens))
    lines.append(tokens_line)

    bonuses_line = Text("Bonuses  (DSERO) :  ", style="bold")
    bonuses_line.append_text(format_cost(player.bonuses))
    lines.append(bonuses_line)

    lines.append(_render_reserved(player))
    lines.append(_render_owned_nobles(player))

    return Panel(Group(*lines), title=title, border_style="green")


def _render_reserved(player: PlayerState) -> Text:
    t = Text("Reserved (+P [B] DSERO): ", style="bold")
    if not player.reserved:
        t.append("(none)", style=DASH_STYLE)
        return t
    for i, card in enumerate(player.reserved):
        if i:
            t.append("   ")
        t.append(f"r{i}: ", style="dim")
        t.append_text(format_card(card))
    return t


def _render_owned_nobles(player: PlayerState) -> Text:
    t = Text("Nobles   (+P DSERO)    : ", style="bold")
    if not player.nobles:
        t.append("(none)", style=DASH_STYLE)
        return t
    for i, n in enumerate(player.nobles):
        if i:
            t.append("   ")
        t.append_text(format_noble(n))
    return t
