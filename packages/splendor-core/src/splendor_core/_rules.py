from __future__ import annotations

import random
from itertools import combinations

from splendor_core._actions import Action, Buy, Reserve, TakeThree, TakeTwo
from splendor_core._cards import ALL_CARDS, ALL_NOBLES, Card
from splendor_core._state import GamePhase, GameState, PlayerState
from splendor_core._types import GEM_COLORS, GemColor, Tokens

_TOKENS_PER_COLOR = {2: 4, 3: 5, 4: 7}
_NOBLES_REVEALED = {2: 3, 3: 4, 4: 5}
_GOLD_COUNT = 5
_VISIBLE_SLOTS = 4
_WIN_THRESHOLD = 15
_MAX_TOKENS = 10
_MAX_RESERVED = 3


def _empty_tokens() -> Tokens:
    return {c: 0 for c in GemColor}


def make_player() -> PlayerState:
    return PlayerState(
        tokens=_empty_tokens(),
        purchased=[],
        reserved=[],
        nobles=[],
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def new_game(num_players: int, seed: int | None = None) -> GameState:
    if num_players not in (2, 3, 4):
        raise ValueError(f"num_players must be 2, 3, or 4 (got {num_players})")

    rng = random.Random(seed)

    bank: Tokens = {c: _TOKENS_PER_COLOR[num_players] for c in GEM_COLORS}
    bank[GemColor.GOLD] = _GOLD_COUNT

    tier_cards: dict[int, list[Card]] = {1: [], 2: [], 3: []}
    for card in ALL_CARDS:
        tier_cards[card.tier].append(card)
    for tier in (1, 2, 3):
        rng.shuffle(tier_cards[tier])

    visible: dict[int, list[Card | None]] = {}
    decks: dict[int, list[Card]] = {}
    for tier in (1, 2, 3):
        deck = tier_cards[tier]
        visible[tier] = [deck.pop() for _ in range(_VISIBLE_SLOTS)]
        decks[tier] = deck

    all_nobles = list(ALL_NOBLES)
    rng.shuffle(all_nobles)
    nobles = all_nobles[: _NOBLES_REVEALED[num_players]]

    players = [make_player() for _ in range(num_players)]

    return GameState(
        bank=bank,
        decks=decks,
        visible=visible,
        nobles=nobles,
        players=players,
        current_player=0,
        turn=0,
        phase=GamePhase.MAIN,
    )


def legal_actions(state: GameState) -> list[Action]:
    if state.phase == GamePhase.FINISHED:
        return []

    player = state.players[state.current_player]
    actions: list[Action] = []

    _add_take_three(state, player, actions)
    _add_take_two(state, player, actions)
    _add_reserve(state, player, actions)
    _add_buy(state, player, actions)

    return actions


def apply_action(
    state: GameState,
    action: Action,
    rng: random.Random | None = None,
) -> None:
    """Modify state in-place. Handles token overflow and noble auto-assignment."""
    if rng is None:
        rng = random.Random()

    player = state.players[state.current_player]

    if isinstance(action, TakeThree):
        _exec_take_three(state, player, action)
    elif isinstance(action, TakeTwo):
        _exec_take_two(state, player, action)
    elif isinstance(action, Reserve):
        _exec_reserve(state, player, action, rng)
    else:
        _exec_buy(state, player, action)

    _handle_token_overflow(state, player, rng)
    _assign_noble(state, player, rng)
    _check_end_of_round(state)


def returns(state: GameState) -> list[float]:
    """Per-player reward: 1.0 for winner(s), 0.0 otherwise. Only valid when FINISHED."""
    if state.phase != GamePhase.FINISHED:
        raise ValueError("returns() called on non-terminal state")

    scores = [(p.prestige, -len(p.purchased), i) for i, p in enumerate(state.players)]
    best = max(scores)
    best_score = (best[0], best[1])
    winners = [i for (prestige, cards, i) in scores if (prestige, cards) == best_score]
    reward = 1.0 / len(winners)
    return [reward if i in winners else 0.0 for i in range(len(state.players))]


# ---------------------------------------------------------------------------
# Legal-action helpers
# ---------------------------------------------------------------------------


def _add_take_three(state: GameState, player: PlayerState, out: list[Action]) -> None:
    available = [c for c in GEM_COLORS if state.bank.get(c, 0) > 0]
    for triple in combinations(available, 3):
        out.append(TakeThree(frozenset(triple)))


def _add_take_two(state: GameState, player: PlayerState, out: list[Action]) -> None:
    for color in GEM_COLORS:
        if state.bank.get(color, 0) >= 4:
            out.append(TakeTwo(color))


def _add_reserve(state: GameState, player: PlayerState, out: list[Action]) -> None:
    if len(player.reserved) >= _MAX_RESERVED:
        return
    for tier in (1, 2, 3):
        for idx, card in enumerate(state.visible[tier]):
            if card is not None:
                out.append(Reserve(tier=tier, index=idx))
        if state.decks[tier]:
            out.append(Reserve(tier=tier, index=None))


def _add_buy(state: GameState, player: PlayerState, out: list[Action]) -> None:
    for tier in (1, 2, 3):
        for idx, card in enumerate(state.visible[tier]):
            if card is not None and can_afford(player, card):
                out.append(Buy(source="table", tier=tier, index=idx))
    for idx, card in enumerate(player.reserved):
        if can_afford(player, card):
            out.append(Buy(source="reserve", tier=card.tier, index=idx))


def can_afford(player: PlayerState, card: Card) -> bool:
    bonuses = player.bonuses
    shortfall = 0
    for color, needed in card.cost.items():
        effective = max(0, needed - bonuses.get(color, 0))
        have = player.tokens.get(color, 0)
        shortfall += max(0, effective - have)
    return shortfall <= player.tokens.get(GemColor.GOLD, 0)


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------


def _exec_take_three(state: GameState, player: PlayerState, action: TakeThree) -> None:
    if len(action.colors) != 3:
        raise ValueError(
            f"TakeThree requires exactly 3 colors, got {len(action.colors)}"
        )
    for color in action.colors:
        if state.bank.get(color, 0) <= 0:
            raise ValueError(
                f"Cannot take {color.value}: bank has no tokens of that color"
            )
    for color in action.colors:
        state.bank[color] -= 1
        player.tokens[color] = player.tokens.get(color, 0) + 1


def _exec_take_two(state: GameState, player: PlayerState, action: TakeTwo) -> None:
    available = state.bank.get(action.color, 0)
    if available < 4:
        raise ValueError(
            f"Cannot take two {action.color.value}: bank has {available} tokens, need at least 4"
        )
    state.bank[action.color] -= 2
    player.tokens[action.color] = player.tokens.get(action.color, 0) + 2


def _exec_reserve(
    state: GameState,
    player: PlayerState,
    action: Reserve,
    rng: random.Random,
) -> None:
    if action.index is None:
        deck = state.decks[action.tier]
        if not deck:
            return
        card = deck.pop()
    else:
        card = state.visible[action.tier][action.index]
        if card is None:
            return
        replacement = _draw_from_deck(state, action.tier)
        state.visible[action.tier][action.index] = replacement

    player.reserved.append(card)

    if state.bank.get(GemColor.GOLD, 0) > 0:
        state.bank[GemColor.GOLD] -= 1
        player.tokens[GemColor.GOLD] = player.tokens.get(GemColor.GOLD, 0) + 1


def _exec_buy(state: GameState, player: PlayerState, action: Buy) -> None:
    if action.source == "table":
        card = state.visible[action.tier][action.index]
        if card is None:
            return
        state.visible[action.tier][action.index] = _draw_from_deck(state, action.tier)
    else:
        card = player.reserved[action.index]
        player.reserved.pop(action.index)

    _pay_for_card(state, player, card)
    player.purchased.append(card)


def _pay_for_card(state: GameState, player: PlayerState, card: Card) -> None:
    bonuses = player.bonuses
    gold_spent = 0
    for color, needed in card.cost.items():
        effective = max(0, needed - bonuses.get(color, 0))
        from_tokens = min(effective, player.tokens.get(color, 0))
        gold_needed = effective - from_tokens
        player.tokens[color] = player.tokens.get(color, 0) - from_tokens
        state.bank[color] = state.bank.get(color, 0) + from_tokens
        gold_spent += gold_needed
    player.tokens[GemColor.GOLD] = player.tokens.get(GemColor.GOLD, 0) - gold_spent
    state.bank[GemColor.GOLD] = state.bank.get(GemColor.GOLD, 0) + gold_spent


def _draw_from_deck(state: GameState, tier: int) -> Card | None:
    deck = state.decks[tier]
    if not deck:
        return None
    return deck.pop()


# ---------------------------------------------------------------------------
# Post-action steps
# ---------------------------------------------------------------------------


def _handle_token_overflow(
    state: GameState,
    player: PlayerState,
    rng: random.Random,
) -> None:
    excess = player.token_count - _MAX_TOKENS
    if excess <= 0:
        return
    held = [
        color
        for color in GemColor
        if player.tokens.get(color, 0) > 0
        for _ in range(player.tokens[color])
    ]
    to_discard = rng.sample(held, excess)
    for color in to_discard:
        player.tokens[color] -= 1
        state.bank[color] = state.bank.get(color, 0) + 1


def _assign_noble(state: GameState, player: PlayerState, rng: random.Random) -> None:
    bonuses = player.bonuses
    eligible = [
        noble
        for noble in state.nobles
        if all(bonuses.get(c, 0) >= n for c, n in noble.requirement.items())
    ]
    if not eligible:
        return
    chosen = rng.choice(eligible) if len(eligible) > 1 else eligible[0]
    state.nobles.remove(chosen)
    player.nobles.append(chosen)


def _check_end_of_round(state: GameState) -> None:
    n = len(state.players)
    next_player = (state.current_player + 1) % n

    if next_player == 0:
        state.turn += 1

    any_triggered = any(p.prestige >= _WIN_THRESHOLD for p in state.players)

    if any_triggered and next_player == 0:
        state.phase = GamePhase.FINISHED
        return

    state.current_player = next_player
