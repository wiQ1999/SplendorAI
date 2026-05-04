from splendor_cli.rendering import (
    format_card,
    format_cost,
    format_noble,
    format_player_tokens,
    format_prestige,
)
from splendor_core import ALL_CARDS, ALL_NOBLES, GemColor


def test_format_cost_dashes_for_zero():
    assert format_cost({}).plain == "-----"


def test_format_cost_keeps_dsero_order():
    cost = {GemColor.DIAMOND: 3, GemColor.RUBY: 2, GemColor.ONYX: 1}
    assert format_cost(cost).plain == "3--21"


def test_format_player_tokens_includes_gold():
    tokens = {GemColor.DIAMOND: 2, GemColor.GOLD: 1}
    assert format_player_tokens(tokens).plain == "2----1"


def test_format_player_tokens_all_dashes_when_empty():
    assert format_player_tokens({}).plain == "------"


def test_format_prestige_zero_is_dash():
    assert format_prestige(0).plain == "+-"


def test_format_prestige_nonzero():
    assert format_prestige(4).plain == "+4"


def test_format_card_layout_is_fixed_width():
    card = next(c for c in ALL_CARDS if c.tier == 1)
    rendered = format_card(card).plain
    assert len(rendered) == 12  # "+P [B] DSERO"
    assert rendered[2] == " "
    assert rendered[3] == "["
    assert rendered[5] == "]"
    assert rendered[6] == " "


def test_format_card_specific_card():
    card = next(
        c
        for c in ALL_CARDS
        if c.bonus == GemColor.RUBY
        and c.cost == {GemColor.DIAMOND: 3}
        and c.prestige == 0
    )
    assert format_card(card).plain == "+- [R] 3----"


def test_format_noble_layout():
    noble = ALL_NOBLES[0]
    rendered = format_noble(noble).plain
    assert len(rendered) == 8  # "+P DSERO"
    assert rendered.startswith("+")
    assert rendered[2] == " "
