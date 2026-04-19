from __future__ import annotations

import enum
from dataclasses import dataclass

from splendor_core._cards import Card, Noble
from splendor_core._types import GEM_COLORS, Tokens


class GamePhase(enum.Enum):
    MAIN = "main"
    FINISHED = "finished"


@dataclass
class PlayerState:
    tokens: Tokens
    purchased: list[Card]
    reserved: list[Card]
    nobles: list[Noble]

    @property
    def bonuses(self) -> Tokens:
        result: Tokens = {c: 0 for c in GEM_COLORS}
        for card in self.purchased:
            result[card.bonus] = result.get(card.bonus, 0) + 1
        return result

    @property
    def prestige(self) -> int:
        return sum(c.prestige for c in self.purchased) + sum(
            n.prestige for n in self.nobles
        )

    @property
    def token_count(self) -> int:
        return sum(self.tokens.values())


@dataclass
class GameState:
    bank: Tokens
    decks: dict[int, list[Card]]
    visible: dict[int, list[Card | None]]
    nobles: list[Noble]
    players: list[PlayerState]
    current_player: int
    turn: int
    phase: GamePhase
