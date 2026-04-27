from splendor_core import GEM_COLORS, GemColor

TAKE_ORDER: tuple[GemColor, ...] = GEM_COLORS

COLOR_STYLE: dict[GemColor, str] = {
    GemColor.DIAMOND: "bright_white on grey30",
    GemColor.SAPPHIRE: "bright_white on blue",
    GemColor.EMERALD: "bright_white on green",
    GemColor.RUBY: "bright_white on red",
    GemColor.ONYX: "bright_white on black",
    GemColor.GOLD: "black on yellow",
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
