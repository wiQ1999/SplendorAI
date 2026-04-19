from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from splendor_core._types import GemColor


@dataclass(frozen=True)
class TakeThree:
    """Take 1 token each of 3 different non-gold colors."""

    colors: frozenset[GemColor]


@dataclass(frozen=True)
class TakeTwo:
    """Take 2 tokens of the same color (bank must have ≥ 4)."""

    color: GemColor


@dataclass(frozen=True)
class Reserve:
    """Reserve a card; receive 1 gold if available.

    index=None means draw blind from the top of the deck.
    """

    tier: int
    index: int | None


@dataclass(frozen=True)
class Buy:
    """Buy a card from the table or from the player's reserve.

    source == "table":   tier identifies the row, index is the visible slot (0-3)
    source == "reserve": index is the position in the player's reserved list (0-2)
                         tier is ignored
    Gold payment is computed automatically by the engine.
    """

    source: Literal["table", "reserve"]
    tier: int
    index: int


Action = TakeThree | TakeTwo | Reserve | Buy
