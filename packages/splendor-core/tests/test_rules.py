import random

import pytest
from splendor_core import (
    Buy,
    GamePhase,
    GemColor,
    Reserve,
    TakeThree,
    TakeTwo,
    apply_action,
    legal_actions,
    new_game,
    returns,
)
from splendor_core._cards import ALL_CARDS, Card
from splendor_core._rules import can_afford, make_player


def test_new_game_2p() -> None:
    state = new_game(2, seed=0)
    assert len(state.players) == 2
    assert len(state.nobles) == 3
    assert state.bank[GemColor.DIAMOND] == 4
    assert state.bank[GemColor.GOLD] == 5
    assert state.phase == GamePhase.MAIN
    assert state.current_player == 0
    assert state.turn == 0


def test_new_game_4p() -> None:
    state = new_game(4, seed=1)
    assert len(state.players) == 4
    assert len(state.nobles) == 5
    assert state.bank[GemColor.DIAMOND] == 7
    assert state.bank[GemColor.GOLD] == 5
    assert state.phase == GamePhase.MAIN
    assert state.current_player == 0
    assert state.turn == 0


def test_new_game_invalid_players() -> None:
    with pytest.raises(ValueError):
        new_game(1)
    with pytest.raises(ValueError):
        new_game(5)


def test_new_game_visible_4_per_tier() -> None:
    state = new_game(2, seed=42)
    for tier in (1, 2, 3):
        visible = [c for c in state.visible[tier] if c is not None]
        assert len(visible) == 4


def test_new_game_deck_sizes() -> None:
    state = new_game(2, seed=7)
    assert len(state.decks[1]) == 36
    assert len(state.decks[2]) == 26
    assert len(state.decks[3]) == 16


def test_new_game_reproducible() -> None:
    s1 = new_game(3, seed=99)
    s2 = new_game(3, seed=99)
    ids1 = [c.id for c in s1.visible[1] if c is not None]
    ids2 = [c.id for c in s2.visible[1] if c is not None]
    assert ids1 == ids2


def test_legal_actions_contains_take_three() -> None:
    state = new_game(2, seed=0)
    actions = legal_actions(state)
    take3 = [a for a in actions if isinstance(a, TakeThree)]
    assert len(take3) > 0


def test_legal_actions_finished_returns_empty() -> None:
    state = new_game(2, seed=0)
    state.phase = GamePhase.FINISHED
    assert legal_actions(state) == []


def test_take_two_requires_4_in_bank() -> None:
    state = new_game(2, seed=0)
    state.bank[GemColor.DIAMOND] = 3
    actions = legal_actions(state)
    take2_diamond = [
        a for a in actions if isinstance(a, TakeTwo) and a.color == GemColor.DIAMOND
    ]
    assert len(take2_diamond) == 0


def test_reserve_blocked_at_3() -> None:
    state = new_game(2, seed=0)
    state.players[0].reserved = list(ALL_CARDS[:3])
    actions = legal_actions(state)
    assert not any(isinstance(a, Reserve) for a in actions)


def test_take_three_moves_tokens() -> None:
    state = new_game(2, seed=0)
    colors = frozenset([GemColor.DIAMOND, GemColor.SAPPHIRE, GemColor.EMERALD])
    apply_action(state, TakeThree(colors), rng=random.Random(0))
    player = state.players[0]
    assert player.tokens[GemColor.DIAMOND] == 1
    assert player.tokens[GemColor.SAPPHIRE] == 1
    assert player.tokens[GemColor.EMERALD] == 1
    assert state.bank[GemColor.DIAMOND] == 3


def test_take_three_advances_player() -> None:
    state = new_game(2, seed=0)
    colors = frozenset([GemColor.DIAMOND, GemColor.SAPPHIRE, GemColor.EMERALD])
    apply_action(state, TakeThree(colors), rng=random.Random(0))
    assert state.current_player == 1


def test_take_two_moves_tokens() -> None:
    state = new_game(4, seed=0)
    apply_action(state, TakeTwo(GemColor.RUBY), rng=random.Random(0))
    assert state.players[0].tokens[GemColor.RUBY] == 2
    assert state.bank[GemColor.RUBY] == 5


def test_reserve_adds_card_and_gold() -> None:
    state = new_game(2, seed=0)
    card = state.visible[1][0]
    assert card is not None
    apply_action(state, Reserve(tier=1, index=0), rng=random.Random(0))
    player = state.players[0]
    assert len(player.reserved) == 1
    assert player.reserved[0].id == card.id
    assert player.tokens[GemColor.GOLD] == 1
    assert state.bank[GemColor.GOLD] == 4


def test_reserve_replaces_visible_slot() -> None:
    state = new_game(2, seed=0)
    old_card = state.visible[1][0]
    apply_action(state, Reserve(tier=1, index=0), rng=random.Random(0))
    assert state.visible[1][0] is not old_card or state.visible[1][0] is None


def test_reserve_blind_from_deck() -> None:
    state = new_game(2, seed=0)
    deck_size_before = len(state.decks[2])
    apply_action(state, Reserve(tier=2, index=None), rng=random.Random(0))
    assert len(state.players[0].reserved) == 1
    assert len(state.decks[2]) == deck_size_before - 1


def test_buy_from_table() -> None:
    state = new_game(2, seed=0)
    player = state.players[0]
    card = next(c for c in state.visible[1] if c is not None)
    for color, amount in card.cost.items():
        player.tokens[color] = amount
    idx = state.visible[1].index(card)
    apply_action(state, Buy(source="table", tier=1, index=idx), rng=random.Random(0))
    assert card in player.purchased
    assert card not in state.visible[1]


def test_buy_from_reserve() -> None:
    state = new_game(2, seed=0)
    player = state.players[0]
    card = state.visible[1][0]
    assert card is not None
    player.reserved.append(card)
    state.visible[1][0] = None
    for color, amount in card.cost.items():
        player.tokens[color] = amount
    apply_action(
        state, Buy(source="reserve", tier=card.tier, index=0), rng=random.Random(0)
    )
    assert card in player.purchased
    assert card not in player.reserved


def test_buy_uses_bonuses() -> None:
    player = make_player()
    bonus_card = Card(id=500, tier=1, bonus=GemColor.RUBY, prestige=0, cost={})
    player.purchased.append(bonus_card)
    player.tokens[GemColor.RUBY] = 1
    target = Card(
        id=501, tier=1, bonus=GemColor.DIAMOND, prestige=0, cost={GemColor.RUBY: 2}
    )
    assert can_afford(player, target)


def test_can_afford_with_gold() -> None:
    player = make_player()
    player.tokens[GemColor.RUBY] = 1
    player.tokens[GemColor.GOLD] = 1
    card = Card(
        id=999, tier=1, bonus=GemColor.DIAMOND, prestige=0, cost={GemColor.RUBY: 2}
    )
    assert can_afford(player, card)


def test_cannot_afford_insufficient() -> None:
    player = make_player()
    player.tokens[GemColor.RUBY] = 1
    card = Card(
        id=998, tier=1, bonus=GemColor.DIAMOND, prestige=0, cost={GemColor.RUBY: 3}
    )
    assert not can_afford(player, card)


def test_token_overflow_capped_at_10() -> None:
    state = new_game(4, seed=0)
    player = state.players[0]
    for color in (GemColor.DIAMOND, GemColor.SAPPHIRE, GemColor.EMERALD):
        player.tokens[color] = 3
    assert player.token_count == 9
    apply_action(state, TakeTwo(GemColor.RUBY), rng=random.Random(42))
    assert player.token_count == 10


def test_game_not_finished_after_first_action() -> None:
    state = new_game(2, seed=0)
    colors = frozenset([GemColor.DIAMOND, GemColor.SAPPHIRE, GemColor.EMERALD])
    apply_action(state, TakeThree(colors), rng=random.Random(0))
    assert state.phase == GamePhase.MAIN


def test_returns_raises_if_not_finished() -> None:
    state = new_game(2, seed=0)
    with pytest.raises(ValueError):
        returns(state)


def test_returns_single_winner() -> None:
    state = new_game(2, seed=0)
    state.phase = GamePhase.FINISHED
    state.players[0].purchased = [
        Card(id=900 + i, tier=1, bonus=GemColor.DIAMOND, prestige=5, cost={})
        for i in range(4)
    ]
    r = returns(state)
    assert r[0] == 1.0
    assert r[1] == 0.0


def test_returns_tie_splits_reward() -> None:
    state = new_game(2, seed=0)
    state.phase = GamePhase.FINISHED
    for p in state.players:
        p.purchased = [
            Card(id=800 + i, tier=1, bonus=GemColor.DIAMOND, prestige=5, cost={})
            for i in range(3)
        ]
    r = returns(state)
    assert abs(r[0] - 0.5) < 1e-9
    assert abs(r[1] - 0.5) < 1e-9
