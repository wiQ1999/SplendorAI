from splendor_core import ALL_CARDS, ALL_NOBLES, GemColor, GEM_COLORS


def test_card_count() -> None:
    assert len(ALL_CARDS) == 90


def test_noble_count() -> None:
    assert len(ALL_NOBLES) == 10


def test_tier_distribution() -> None:
    by_tier = {1: 0, 2: 0, 3: 0}
    for c in ALL_CARDS:
        by_tier[c.tier] += 1
    assert by_tier[1] == 40
    assert by_tier[2] == 30
    assert by_tier[3] == 20


def test_bonus_distribution_tier1() -> None:
    tier1 = [c for c in ALL_CARDS if c.tier == 1]
    for color in GEM_COLORS:
        assert sum(1 for c in tier1 if c.bonus == color) == 8


def test_no_gold_bonus() -> None:
    for c in ALL_CARDS:
        assert c.bonus != GemColor.GOLD


def test_no_gold_in_cost() -> None:
    for c in ALL_CARDS:
        assert GemColor.GOLD not in c.cost


def test_noble_prestige() -> None:
    for n in ALL_NOBLES:
        assert n.prestige == 3


def test_card_ids_unique() -> None:
    ids = [c.id for c in ALL_CARDS]
    assert len(ids) == len(set(ids))
