from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict, cast

from splendor_core._types import GemColor, Tokens

_DATA_DIR = Path(__file__).parent / "data"


class _CardEntry(TypedDict):
    id: int
    tier: int
    bonus: str
    prestige: int
    cost: dict[str, int]


class _NobleEntry(TypedDict):
    id: int
    prestige: int
    requirement: dict[str, int]


@dataclass(frozen=True)
class Card:
    id: int
    tier: int = field(compare=False)
    bonus: GemColor = field(compare=False)
    prestige: int = field(compare=False)
    cost: Tokens = field(compare=False)


@dataclass(frozen=True)
class Noble:
    id: int
    prestige: int = field(compare=False)
    requirement: Tokens = field(compare=False)


def _load_cards() -> tuple[Card, ...]:
    raw = cast(
        list[_CardEntry],
        json.loads((_DATA_DIR / "cards.json").read_text(encoding="utf-8")),
    )
    return tuple(
        Card(
            id=entry["id"],
            tier=entry["tier"],
            bonus=GemColor(entry["bonus"]),
            prestige=entry["prestige"],
            cost={GemColor(c): n for c, n in entry["cost"].items()},
        )
        for entry in raw
    )


def _load_nobles() -> tuple[Noble, ...]:
    raw = cast(
        list[_NobleEntry],
        json.loads((_DATA_DIR / "nobles.json").read_text(encoding="utf-8")),
    )
    return tuple(
        Noble(
            id=entry["id"],
            prestige=entry["prestige"],
            requirement={GemColor(c): n for c, n in entry["requirement"].items()},
        )
        for entry in raw
    )


ALL_CARDS: tuple[Card, ...] = _load_cards()
ALL_NOBLES: tuple[Noble, ...] = _load_nobles()
