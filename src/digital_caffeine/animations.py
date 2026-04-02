"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

# -- Steam frames (4 frames, each 2 lines tall) ------------------------------
# Characters cycle upward to create a rising-steam illusion.

STEAM_FRAMES: list[str] = [
    "    ~ ~  \n   ( _ ) ",
    "   ( _ ) \n    ~ ~  ",
    "   ~ . ~ \n  (  ~  )",
    "  (  ~  )\n   ~ . ~ ",
]

_BLANK_STEAM: str = "         \n         "


def get_steam_frame(elapsed: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A two-line string of steam art, or blank lines if paused.
    """
    if paused:
        return _BLANK_STEAM
    return STEAM_FRAMES[elapsed % len(STEAM_FRAMES)]


# -- Cup art ------------------------------------------------------------------

_CUP_ACTIVE: str = (
    "   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510 \u2510\n"
    "   \u2502\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2502 \u2502\n"
    "   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518 \u2518"
)

_CUP_PAUSED: str = (
    "   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510 \u2510\n"
    "   \u2502\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2502 \u2502\n"
    "   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518 \u2518"
)


def get_cup_art(*, paused: bool) -> str:
    """Return the coffee cup ASCII art.

    Args:
        paused: Whether the engine is paused (shows dim fill).

    Returns:
        A three-line string of cup art.
    """
    return _CUP_PAUSED if paused else _CUP_ACTIVE


# -- Border colors (4-step breathing cycle) -----------------------------------

BORDER_COLORS: list[str] = ["cyan", "dark_cyan", "bright_cyan", "dark_cyan"]


def get_border_color(elapsed: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A Rich color name string.
    """
    if paused:
        return "yellow"
    return BORDER_COLORS[elapsed % len(BORDER_COLORS)]


# -- Quips --------------------------------------------------------------------

QUIPS: list[str] = [
    "Brewing productivity...",
    "Your PC is caffeinated",
    "Sleep is for the weak (and not this PC)",
    "Keeping things percolating...",
    "Another cup? Don't mind if I do",
    "Drip, drip, drip... staying awake",
    "Freshly brewed and wide awake",
    "No decaf allowed here",
    "Espresso yourself freely",
    "A latte work getting done today",
    "Grounds for staying awake",
    "This machine runs on caffeine",
]

PAUSED_QUIP: str = "Gone cold... resume to reheat"


def get_quip(elapsed: int, *, paused: bool) -> str:
    """Return the current quip message.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A quip string.
    """
    if paused:
        return PAUSED_QUIP
    return QUIPS[(elapsed // 8) % len(QUIPS)]
