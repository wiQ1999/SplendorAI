from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text
from splendor_core import (
    Action,
    Buy,
    GameState,
    Reserve,
    TakeThree,
    TakeTwo,
    legal_actions,
)

from splendor_cli.colors import COLOR_STYLE, TAKE_ORDER


class CommandError(Exception):
    pass


@dataclass(frozen=True)
class ParseResult:
    action: Action | None
    exit: bool


@dataclass(frozen=True)
class Suggestion:
    text: Text
    completion: str


COMMAND_NAMES: tuple[str, ...] = ("take", "buy", "reserve", "exit")


def parse_command(raw: str, state: GameState) -> ParseResult:
    tokens = raw.strip().split()
    if not tokens:
        raise CommandError("Empty command")

    cmd = tokens[0].lower()
    args = tokens[1:]

    if cmd == "exit" or cmd == "quit":
        if args:
            raise CommandError("'exit' takes no arguments")
        return ParseResult(action=None, exit=True)

    if cmd == "take":
        return ParseResult(action=_parse_take(args), exit=False)

    if cmd == "buy":
        return ParseResult(action=_parse_buy(args, state), exit=False)

    if cmd == "reserve":
        return ParseResult(action=_parse_reserve(args, state), exit=False)

    raise CommandError(f"Unknown command: {cmd!r}")


def _parse_take(args: list[str]) -> Action:
    if len(args) != 1:
        raise CommandError("Usage: take <5 digits, e.g. 11100 or 00200>")
    digits = args[0]
    if len(digits) != 5 or not digits.isdigit():
        raise CommandError("take expects exactly 5 digits (order: D S E R O)")

    counts = [int(ch) for ch in digits]
    total = sum(counts)

    if total == 3 and all(c in (0, 1) for c in counts):
        colors = frozenset(TAKE_ORDER[i] for i, c in enumerate(counts) if c == 1)
        if len(colors) != 3:
            raise CommandError("take three: must pick 3 different colors (three 1s)")
        return TakeThree(colors=colors)

    if total == 2 and counts.count(2) == 1:
        idx = counts.index(2)
        return TakeTwo(color=TAKE_ORDER[idx])

    raise CommandError("take: use three 1s (e.g. 11100) or a single 2 (e.g. 00200)")


def _parse_buy(args: list[str], state: GameState) -> Action:
    if len(args) != 2:
        raise CommandError("Usage: buy t<tier> <index>   |   buy r <index>")

    source = args[0].lower()
    try:
        index = int(args[1])
    except ValueError as exc:
        raise CommandError("buy: index must be an integer") from exc

    if source == "r":
        player = state.players[state.current_player]
        if not 0 <= index < len(player.reserved):
            raise CommandError(f"buy r: reserve index {index} out of range")
        card = player.reserved[index]
        return Buy(source="reserve", tier=card.tier, index=index)

    if source in ("t1", "t2", "t3"):
        tier = int(source[1])
        if not 0 <= index < len(state.visible[tier]):
            raise CommandError(f"buy {source}: index {index} out of range")
        if state.visible[tier][index] is None:
            raise CommandError(f"buy {source} {index}: slot is empty")
        return Buy(source="table", tier=tier, index=index)

    raise CommandError(f"buy: unknown source {source!r} (use t1/t2/t3 or r)")


def _parse_reserve(args: list[str], state: GameState) -> Action:
    if not 1 <= len(args) <= 2:
        raise CommandError(
            "Usage: reserve t<tier> [<index>]  (omit index for blind draw)"
        )
    tier_tok = args[0].lower()
    if tier_tok not in ("t1", "t2", "t3"):
        raise CommandError("reserve: tier must be t1/t2/t3")
    tier = int(tier_tok[1])

    if len(args) == 1:
        if not state.decks[tier]:
            raise CommandError(f"reserve {tier_tok}: deck is empty")
        return Reserve(tier=tier, index=None)

    try:
        index = int(args[1])
    except ValueError as exc:
        raise CommandError("reserve: index must be an integer") from exc

    if not 0 <= index < len(state.visible[tier]):
        raise CommandError(f"reserve {tier_tok}: index {index} out of range")
    if state.visible[tier][index] is None:
        raise CommandError(f"reserve {tier_tok} {index}: slot is empty")

    return Reserve(tier=tier, index=index)


# ---------------------------------------------------------------------------
# Suggestions
# ---------------------------------------------------------------------------


_MAX_SUGGESTIONS = 12


def build_suggestions(raw: str, state: GameState) -> list[Suggestion]:
    stripped = raw.lstrip()
    lowered = stripped.lower()

    if not stripped or " " not in stripped:
        return _suggest_command_names(lowered)

    cmd, _, rest = stripped.partition(" ")
    cmd_lower = cmd.lower()

    if cmd_lower == "take":
        return _suggest_take(rest, state)
    if cmd_lower == "buy":
        return _suggest_buy(rest, state)
    if cmd_lower == "reserve":
        return _suggest_reserve(rest, state)
    if cmd_lower == "exit" or cmd_lower == "quit":
        return []

    return []


def _suggest_command_names(prefix: str) -> list[Suggestion]:
    out: list[Suggestion] = []
    for name in COMMAND_NAMES:
        if name.startswith(prefix):
            label = Text()
            label.append(name, style="bold cyan")
            label.append(_COMMAND_HINTS[name], style="dim")
            out.append(Suggestion(text=label, completion=name + " "))
    return out


_COMMAND_HINTS: dict[str, str] = {
    "take": "  <5 digits>       take tokens (e.g. 11100, 00200)",
    "buy": "   t<tier> <i> | r <i>   buy a card",
    "reserve": " t<tier> [<i>]        reserve a card (blind if no index)",
    "exit": "                       quit the game",
}


def _suggest_take(rest: str, state: GameState) -> list[Suggestion]:
    rest = rest.strip()
    legal = legal_actions(state)

    options: list[tuple[str, Action]] = []
    for action in legal:
        if isinstance(action, TakeThree):
            pattern = _take_three_pattern(action)
            options.append((pattern, action))
        elif isinstance(action, TakeTwo):
            pattern = _take_two_pattern(action)
            options.append((pattern, action))

    options = [(p, a) for p, a in options if p.startswith(rest)]
    options.sort(key=lambda pa: pa[0])

    out: list[Suggestion] = []
    for pattern, _ in options[:_MAX_SUGGESTIONS]:
        out.append(
            Suggestion(
                text=_render_take_line(pattern, rest),
                completion=f"take {pattern}",
            )
        )
    return out


def _take_three_pattern(action: TakeThree) -> str:
    digits = ["1" if c in action.colors else "0" for c in TAKE_ORDER]
    return "".join(digits)


def _take_two_pattern(action: TakeTwo) -> str:
    digits = ["2" if c == action.color else "0" for c in TAKE_ORDER]
    return "".join(digits)


def _render_take_line(pattern: str, typed: str) -> Text:
    line = Text()
    line.append("take ", style="bold cyan")
    for i, digit in enumerate(pattern):
        color = TAKE_ORDER[i]
        if digit == "0":
            style = "dim"
        else:
            style = COLOR_STYLE[color]
        is_typed = i < len(typed) and typed[i] == digit
        line.append(digit, style=f"{style}{' underline' if is_typed else ''}")
    line.append("   ", style="")
    parts: list[str] = []
    for i, digit in enumerate(pattern):
        if digit != "0":
            color = TAKE_ORDER[i]
            parts.append(f"{digit}×{color.value}")
    line.append("  ".join(parts), style="dim")
    return line


def _suggest_buy(rest: str, state: GameState) -> list[Suggestion]:
    from splendor_cli.rendering import format_card

    rest_lower = rest.strip().lower()
    legal = [a for a in legal_actions(state) if isinstance(a, Buy)]

    out: list[Suggestion] = []
    for action in legal:
        if action.source == "table":
            arg = f"t{action.tier} {action.index}"
            card = state.visible[action.tier][action.index]
            assert card is not None
        else:
            arg = f"r {action.index}"
            player = state.players[state.current_player]
            card = player.reserved[action.index]

        if not arg.startswith(rest_lower):
            continue

        line = Text()
        line.append("buy ", style="bold cyan")
        line.append(arg, style="white")
        line.append(f"   T{card.tier}  ", style="dim")
        line.append_text(format_card(card))
        out.append(Suggestion(text=line, completion=f"buy {arg}"))

        if len(out) >= _MAX_SUGGESTIONS:
            break
    return out


def _suggest_reserve(rest: str, state: GameState) -> list[Suggestion]:
    from splendor_cli.rendering import format_card

    rest_lower = rest.strip().lower()
    legal = [a for a in legal_actions(state) if isinstance(a, Reserve)]

    out: list[Suggestion] = []
    for action in legal:
        line = Text()
        line.append("reserve ", style="bold cyan")
        if action.index is None:
            arg = f"t{action.tier}"
            if not arg.startswith(rest_lower):
                continue
            line.append(arg, style="white")
            line.append(f"     blind draw from tier {action.tier} deck", style="dim")
        else:
            arg = f"t{action.tier} {action.index}"
            if not arg.startswith(rest_lower):
                continue
            card = state.visible[action.tier][action.index]
            assert card is not None
            line.append(arg, style="white")
            line.append(f"   T{card.tier}  ", style="dim")
            line.append_text(format_card(card))

        out.append(Suggestion(text=line, completion=f"reserve {arg}"))

        if len(out) >= _MAX_SUGGESTIONS:
            break
    return out
