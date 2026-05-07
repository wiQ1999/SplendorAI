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

# Pre-computed singletons — avoids allocating new TakeThree/TakeTwo objects on
# every legal_actions() call. Tuples from combinations() match the key type
# because available is always built by filtering GEM_COLORS in order.
_TAKE_THREE_ACTIONS: dict[tuple[GemColor, ...], TakeThree] = {
    triple: TakeThree(frozenset(triple)) for triple in combinations(GEM_COLORS, 3)
}
_TAKE_TWO_ACTIONS: dict[GemColor, TakeTwo] = {
    color: TakeTwo(color) for color in GEM_COLORS
}


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
    # Filter preserves GEM_COLORS order, so tuples from combinations() are valid keys.
    available = [c for c in GEM_COLORS if state.bank[c] > 0]
    for triple in combinations(available, 3):
        out.append(_TAKE_THREE_ACTIONS[triple])


def _add_take_two(state: GameState, player: PlayerState, out: list[Action]) -> None:
    for color in GEM_COLORS:
        if state.bank[color] >= 4:
            out.append(_TAKE_TWO_ACTIONS[color])


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
    bonuses = player.bonuses  # O(1) read; hoist out of the card loop
    gold = player.tokens[GemColor.GOLD]
    tokens = player.tokens
    for tier in (1, 2, 3):
        for idx, card in enumerate(state.visible[tier]):
            if card is not None and _can_afford_with(tokens, bonuses, gold, card):
                out.append(Buy(source="table", tier=tier, index=idx))
    for idx, card in enumerate(player.reserved):
        if _can_afford_with(tokens, bonuses, gold, card):
            out.append(Buy(source="reserve", tier=card.tier, index=idx))


def _can_afford_with(tokens: Tokens, bonuses: Tokens, gold: int, card: Card) -> bool:
    shortfall = 0
    for color, needed in card.cost.items():
        effective = needed - bonuses[color]
        if effective > 0:
            deficit = effective - tokens[color]
            if deficit > 0:
                shortfall += deficit
    return shortfall <= gold


def can_afford(player: PlayerState, card: Card) -> bool:
    bonuses = player.bonuses
    return _can_afford_with(player.tokens, bonuses, player.tokens[GemColor.GOLD], card)


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------


def _exec_take_three(state: GameState, player: PlayerState, action: TakeThree) -> None:
    if len(action.colors) != 3:
        raise ValueError(
            f"TakeThree requires exactly 3 colors, got {len(action.colors)}"
        )
    for color in action.colors:
        if state.bank[color] <= 0:
            raise ValueError(
                f"Cannot take {color.value}: bank has no tokens of that color"
            )
    for color in action.colors:
        state.bank[color] -= 1
        player.tokens[color] += 1


def _exec_take_two(state: GameState, player: PlayerState, action: TakeTwo) -> None:
    available = state.bank[action.color]
    if available < 4:
        raise ValueError(
            f"Cannot take two {action.color.value}: bank has {available} tokens,"
            " need at least 4"
        )
    state.bank[action.color] -= 2
    player.tokens[action.color] += 2


def _exec_reserve(
    state: GameState,
    player: PlayerState,
    action: Reserve,
    rng: random.Random,
) -> None:
    if len(player.reserved) >= _MAX_RESERVED:
        raise ValueError(
            f"Cannot reserve: player already holds {_MAX_RESERVED} reserved cards"
        )
    if action.tier not in (1, 2, 3):
        raise ValueError(f"Reserve tier must be 1, 2, or 3 (got {action.tier})")

    if action.index is None:
        deck = state.decks[action.tier]
        if not deck:
            raise ValueError(
                f"Cannot reserve blind from tier {action.tier}: deck is empty"
            )
        card = deck.pop()
    else:
        visible_row = state.visible[action.tier]
        if not 0 <= action.index < len(visible_row):
            raise ValueError(
                f"Reserve index {action.index} out of range for tier {action.tier}"
            )
        card = visible_row[action.index]
        if card is None:
            raise ValueError(
                f"Cannot reserve tier {action.tier} slot {action.index}: slot is empty"
            )
        state.visible[action.tier][action.index] = _draw_from_deck(state, action.tier)

    player.reserved.append(card)

    if state.bank[GemColor.GOLD] > 0:
        state.bank[GemColor.GOLD] -= 1
        player.tokens[GemColor.GOLD] += 1


def _exec_buy(state: GameState, player: PlayerState, action: Buy) -> None:
    if action.source == "table":
        if action.tier not in (1, 2, 3):
            raise ValueError(f"Buy tier must be 1, 2, or 3 (got {action.tier})")
        visible_row = state.visible[action.tier]
        if not 0 <= action.index < len(visible_row):
            raise ValueError(
                f"Buy index {action.index} out of range for tier {action.tier}"
            )
        card = visible_row[action.index]
        if card is None:
            raise ValueError(
                f"Cannot buy tier {action.tier} slot {action.index}: slot is empty"
            )
        if not _can_afford_with(
            player.tokens, player.bonuses, player.tokens[GemColor.GOLD], card
        ):
            raise ValueError(
                f"Cannot afford card at tier {action.tier} slot {action.index}"
            )
        state.visible[action.tier][action.index] = _draw_from_deck(state, action.tier)
    else:
        if not 0 <= action.index < len(player.reserved):
            raise ValueError(
                f"Buy reserve index {action.index} out of range"
                f" (player has {len(player.reserved)} reserved cards)"
            )
        card = player.reserved[action.index]
        if not _can_afford_with(
            player.tokens, player.bonuses, player.tokens[GemColor.GOLD], card
        ):
            raise ValueError(f"Cannot afford reserved card at index {action.index}")
        player.reserved.pop(action.index)

    _pay_for_card(state, player, card, player.bonuses)
    player.add_purchased(card)


def _pay_for_card(
    state: GameState, player: PlayerState, card: Card, bonuses: Tokens
) -> None:
    gold_spent = 0
    for color, needed in card.cost.items():
        effective = max(0, needed - bonuses[color])
        from_tokens = min(effective, player.tokens[color])
        gold_needed = effective - from_tokens
        player.tokens[color] -= from_tokens
        state.bank[color] += from_tokens
        gold_spent += gold_needed
    player.tokens[GemColor.GOLD] -= gold_spent
    state.bank[GemColor.GOLD] += gold_spent


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
        if player.tokens[color] > 0
        for _ in range(player.tokens[color])
    ]
    to_discard = rng.sample(held, excess)
    for color in to_discard:
        player.tokens[color] -= 1
        state.bank[color] += 1


def _assign_noble(state: GameState, player: PlayerState, rng: random.Random) -> None:
    bonuses = player.bonuses
    eligible_idx = [
        i
        for i, noble in enumerate(state.nobles)
        if all(bonuses[c] >= n for c, n in noble.requirement.items())
    ]
    if not eligible_idx:
        return
    chosen_idx = rng.choice(eligible_idx) if len(eligible_idx) > 1 else eligible_idx[0]
    noble = state.nobles.pop(chosen_idx)
    player.nobles.append(noble)


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
