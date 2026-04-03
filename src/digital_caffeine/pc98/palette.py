"""PC-98 16-color palette with cycling and ordered dithering."""

from __future__ import annotations

# -- 16-color warm PC-98 palette ---------------------------------------------

PALETTE: list[str] = [
    "#000000",  # 0  Black
    "#1A0A2E",  # 1  Deep Navy
    "#3A1A06",  # 2  Dark Brown
    "#8B4513",  # 3  Warm Brown
    "#B8520A",  # 4  Chocolate
    "#D2691E",  # 5  Amber
    "#FFB347",  # 6  Gold
    "#FFDEAD",  # 7  Cream
    "#8B0000",  # 8  Deep Red
    "#AA3377",  # 9  Magenta
    "#CC8899",  # 10 Dusty Rose
    "#4477AA",  # 11 Steel Blue
    "#556677",  # 12 Slate
    "#887766",  # 13 Warm Gray
    "#CCBBAA",  # 14 Light Gray
    "#EEDDCC",  # 15 Off-White
]

PALETTE_RGB: list[tuple[int, int, int]] = [
    (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)) for c in PALETTE
]

# Palette index aliases for readability in sprite code
BLACK = 0
DEEP_NAVY = 1
DARK_BROWN = 2
WARM_BROWN = 3
CHOCOLATE = 4
AMBER = 5
GOLD = 6
CREAM = 7
DEEP_RED = 8
MAGENTA = 9
DUSTY_ROSE = 10
STEEL_BLUE = 11
SLATE = 12
WARM_GRAY = 13
LIGHT_GRAY = 14
OFF_WHITE = 15

# -- 2x2 Bayer ordered dither matrix -----------------------------------------

_BAYER_2X2 = [
    [0, 2],
    [3, 1],
]


def dither_pick(color_a: int, color_b: int, x: int, y: int) -> int:
    """Pick between two palette indices using 2x2 ordered dithering.

    Returns color_a or color_b based on pixel position in the Bayer matrix.
    Produces a ~50/50 checkerboard blend at the 2x2 scale.
    """
    if color_a == color_b:
        return color_a
    threshold = _BAYER_2X2[y % 2][x % 2]
    return color_a if threshold < 2 else color_b


# -- Palette cycling ----------------------------------------------------------

# Cycling groups: tuples of palette indices that rotate together
_COFFEE_CYCLE = (5, 6, 7)    # Amber, Gold, Cream - liquid shimmer
_STEAM_CYCLE = (12, 13, 1)   # Slate, Warm Gray, Deep Navy - steam fade

_COFFEE_RATE = 4   # Rotate every N frames
_STEAM_RATE = 6    # Rotate every N frames


class CyclePalette:
    """Manages palette cycling for animation.

    Maintains frame counter and rotates cycling groups at their
    configured rates. Non-cycling indices always return base palette.
    """

    def __init__(self) -> None:
        self._frame = 0
        self._coffee_offset = 0
        self._steam_offset = 0

    def advance(self) -> None:
        """Advance one frame. Rotates cycling groups at their rates."""
        self._frame += 1
        if self._frame % _COFFEE_RATE == 0:
            self._coffee_offset = (self._coffee_offset + 1) % len(_COFFEE_CYCLE)
        if self._frame % _STEAM_RATE == 0:
            self._steam_offset = (self._steam_offset + 1) % len(_STEAM_CYCLE)

    def get_rgb(self, index: int) -> tuple[int, int, int]:
        """Return the current RGB for a palette index, accounting for cycling."""
        mapped = self._map_index(index)
        return PALETTE_RGB[mapped]

    def get_hex(self, index: int) -> str:
        """Return the current hex color for a palette index."""
        mapped = self._map_index(index)
        return PALETTE[mapped]

    def get_rgb_darkened(self, index: int, factor: float) -> tuple[int, int, int]:
        """Return darkened RGB for scanline effect."""
        r, g, b = self.get_rgb(index)
        return (int(r * factor), int(g * factor), int(b * factor))

    def build_pillow_palette(self) -> list[int]:
        """Build a flat RGB palette list for Pillow Image.putpalette().

        Returns a 768-element list (256 entries x 3 channels).
        """
        pal = [0] * 768
        for i in range(16):
            r, g, b = self.get_rgb(i)
            pal[i * 3] = r
            pal[i * 3 + 1] = g
            pal[i * 3 + 2] = b
        return pal

    def _map_index(self, index: int) -> int:
        """Map a palette index through any active cycling."""
        if index in _COFFEE_CYCLE:
            pos = _COFFEE_CYCLE.index(index)
            return _COFFEE_CYCLE[(pos + self._coffee_offset) % len(_COFFEE_CYCLE)]
        if index in _STEAM_CYCLE:
            pos = _STEAM_CYCLE.index(index)
            return _STEAM_CYCLE[(pos + self._steam_offset) % len(_STEAM_CYCLE)]
        return index
