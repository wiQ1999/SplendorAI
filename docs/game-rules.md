# Game rules — Splendor

Reference spec for implementing `splendor-core`. Source: official Splendor rulebook (Space Cowboys, 2014).

## Components

- **Tokens:** 7× each gem color (emerald, diamond, sapphire, onyx, ruby) + 5× gold joker
- **Cards:** 40 level-1, 30 level-2, 20 level-3 development cards
- **Nobles:** 10 noble tiles (3 prestige points each)

## Setup

- Shuffle each card deck separately; arrange in 3 face-down piles (level 1 at top, level 3 at bottom).
- Reveal 4 cards from each level.
- Reveal `num_players + 1` noble tiles; remove the rest from the game.
- Place tokens in 6 separate piles accessible to all players.

| Players | Tokens per gem color | Noble tiles revealed |
|---|---|---|
| 2 | 4 | 3 |
| 3 | 5 | 4 |
| 4 | 7 | 5 |

Gold joker count is always 5, regardless of player count.

## Turn structure

The youngest player goes first; play proceeds clockwise.
Each player performs **exactly one** of the following four actions per turn.

### Actions

**TAKE_THREE** — take 1 token each of 3 different gem colors (not gold).
Each chosen color stack must be non-empty.

**TAKE_TWO** — take 2 tokens of the same gem color.
The chosen color stack must have ≥ 4 tokens *before* the action.

**RESERVE** — take 1 development card; receive 1 gold joker (if available).
- Card may be face-up from the table or drawn blind from the top of any deck.
- Blind-drawn cards are not shown to other players.
- A player may hold at most 3 reserved cards; reserved cards cannot be discarded.
- If no gold jokers remain, the reservation still happens but no token is awarded.

**BUY** — purchase 1 face-up card from the table or 1 previously reserved card.
- Cost = card cost − player's bonuses of matching colors.
- Gold jokers cover any remaining shortfall (1 joker = 1 token of any color).
- Spent tokens (including jokers) return to the supply.
- When a card is taken from the table, immediately replace it with the top card of the same level deck (if the deck is empty, the slot stays empty).

## Tokens

- A player may never hold more than **10 tokens** at end of turn (jokers included).
- If the limit is exceeded, the player must return tokens of their choice until 10 remain.
- All tokens held by a player must be visible to all players at all times.

## Bonuses

Each purchased card provides a permanent bonus of its gem color.
A bonus of color C counts as 1 token of color C when paying for future cards.
Bonuses can reduce a card's cost to 0; a player may buy a card spending no tokens at all.

## Nobles

Checked automatically at the **end of each turn**, after the action.
A player receives a noble visit if their bonuses (not tokens) meet the noble's requirements.

- A player cannot refuse a noble visit.
- Receiving a noble is not an action and does not cost a turn.
- If multiple nobles qualify, the player chooses one.
- At most **one noble per turn**.
- Each noble tile is worth **3 prestige points**.

## End of game

Triggered when any player reaches **≥ 15 prestige points**.
Complete the current round so every player has taken the same number of turns.

**Winner:** player with the most prestige points after the final round.
**Tiebreaker:** fewest development cards purchased wins.
