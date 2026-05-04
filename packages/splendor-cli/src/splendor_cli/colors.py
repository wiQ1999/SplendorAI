from splendor_core import GEM_COLORS, GemColor

TAKE_ORDER: tuple[GemColor, ...] = GEM_COLORS

COLOR_STYLE: dict[GemColor, str] = {
    GemColor.DIAMOND: "bright_white",
    GemColor.SAPPHIRE: "blue",
    GemColor.EMERALD: "green",
    GemColor.RUBY: "red",
    GemColor.ONYX: "grey50",
    GemColor.GOLD: "yellow",
}

COLOR_LETTER: dict[GemColor, str] = {
    GemColor.DIAMOND: "D",
    GemColor.SAPPHIRE: "S",
    GemColor.EMERALD: "E",
    GemColor.RUBY: "R",
    GemColor.ONYX: "O",
    GemColor.GOLD: "G",
}

COLOR_NAME: dict[GemColor, str] = {
    GemColor.DIAMOND: "Diamond",
    GemColor.SAPPHIRE: "Sapphire",
    GemColor.EMERALD: "Emerald",
    GemColor.RUBY: "Ruby",
    GemColor.ONYX: "Onyx",
    GemColor.GOLD: "Gold",
}
