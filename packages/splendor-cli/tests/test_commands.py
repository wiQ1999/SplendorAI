import pytest
from splendor_core import Buy, GemColor, Reserve, TakeThree, TakeTwo, new_game

from splendor_cli.commands import (
    CommandError,
    build_suggestions,
    parse_command,
)


def test_parse_take_three():
    state = new_game(3, seed=0)
    result = parse_command("take 11100", state)
    assert result.exit is False
    assert isinstance(result.action, TakeThree)
    assert result.action.colors == frozenset(
        {GemColor.DIAMOND, GemColor.SAPPHIRE, GemColor.EMERALD}
    )


def test_parse_take_two():
    state = new_game(3, seed=0)
    result = parse_command("take 00200", state)
    assert isinstance(result.action, TakeTwo)
    assert result.action.color == GemColor.EMERALD


def test_parse_take_invalid_pattern():
    state = new_game(3, seed=0)
    with pytest.raises(CommandError):
        parse_command("take 11110", state)


def test_parse_buy_table():
    state = new_game(3, seed=0)
    result = parse_command("buy t1 0", state)
    assert isinstance(result.action, Buy)
    assert result.action.source == "table"
    assert result.action.tier == 1
    assert result.action.index == 0


def test_parse_reserve_blind():
    state = new_game(3, seed=0)
    result = parse_command("reserve t2", state)
    assert isinstance(result.action, Reserve)
    assert result.action.tier == 2
    assert result.action.index is None


def test_parse_exit():
    state = new_game(3, seed=0)
    assert parse_command("exit", state).exit is True
    assert parse_command("quit", state).exit is True


def test_parse_unknown():
    state = new_game(3, seed=0)
    with pytest.raises(CommandError):
        parse_command("foo", state)


def test_suggestions_empty_shows_all_commands():
    state = new_game(3, seed=0)
    names = {s.completion.strip() for s in build_suggestions("", state)}
    assert {"take", "buy", "reserve", "exit"} <= names


def test_suggestions_take_filters_by_prefix():
    state = new_game(3, seed=0)
    all_take = build_suggestions("take ", state)
    assert len(all_take) > 0
    for s in all_take:
        assert s.completion.startswith("take ")

    filtered = build_suggestions("take 1", state)
    assert len(filtered) > 0
    for s in filtered:
        completion_digits = s.completion.removeprefix("take ")
        assert completion_digits.startswith("1")


def test_suggestions_buy_only_shows_affordable():
    state = new_game(3, seed=0)
    assert build_suggestions("buy ", state) == []
