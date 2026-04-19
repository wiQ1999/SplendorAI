import enum


class GemColor(enum.Enum):
    DIAMOND = "diamond"
    SAPPHIRE = "sapphire"
    EMERALD = "emerald"
    RUBY = "ruby"
    ONYX = "onyx"
    GOLD = "gold"


GEM_COLORS: tuple[GemColor, ...] = (
    GemColor.DIAMOND,
    GemColor.SAPPHIRE,
    GemColor.EMERALD,
    GemColor.RUBY,
    GemColor.ONYX,
)

Tokens = dict[GemColor, int]
