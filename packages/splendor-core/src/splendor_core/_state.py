from __future__ import annotations

import enum
from dataclasses import dataclass, field

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
    # Maintained incrementally via add_purchased(); never mutate purchased directly
    # from outside if bonuses accuracy matters.
    _bonuses: Tokens = field(
        default_factory=lambda: {c: 0 for c in GEM_COLORS},
        init=False,
        repr=False,
        compare=False,
    )

    def add_purchased(self, card: Card) -> None:
        """Append a purchased card and update the bonus cache in O(1)."""
        self.purchased.append(card)
        self._bonuses[card.bonus] += 1

    @property
    def bonuses(self) -> Tokens:
        return self._bonuses

    @property
    def prestige(self) -> int:
        return sum(c.prestige for c in self.purchased) + sum(
            n.prestige for n in self.nobles
        )

    @property
    def token_count(self) -> int:
        return sum(self.tokens.values())

    def __deepcopy__(self, memo: dict[int, object]) -> PlayerState:
        # Card and Noble are frozen dataclasses — immutable, safe to share references.
        new = object.__new__(PlayerState)
        new.tokens = self.tokens.copy()
        new.purchased = self.purchased[:]
        new.reserved = self.reserved[:]
        new.nobles = self.nobles[:]
        new._bonuses = self._bonuses.copy()
        return new


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

    def __deepcopy__(self, memo: dict[int, object]) -> GameState:
        # Card and Noble are frozen dataclasses — immutable, safe to share references.
        # Only the mutable containers need copying.
        new = object.__new__(GameState)
        new.bank = self.bank.copy()
        new.decks = {tier: deck[:] for tier, deck in self.decks.items()}
        new.visible = {tier: row[:] for tier, row in self.visible.items()}
        new.nobles = self.nobles[:]
        new.players = [p.__deepcopy__({}) for p in self.players]
        new.current_player = self.current_player
        new.turn = self.turn
        new.phase = self.phase
        return new
