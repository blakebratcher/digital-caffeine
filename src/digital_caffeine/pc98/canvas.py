"""Half-block pixel canvas: renders a Pillow palette Image as Rich Text."""

from __future__ import annotations

from PIL import Image
from rich.style import Style
from rich.text import Text

from digital_caffeine.pc98.palette import PALETTE_RGB, CyclePalette

_UPPER_HALF = "\u2580"
_FULL_BLOCK = "\u2588"
_SPACE = " "

_SCANLINE_FACTOR = 0.8


class PixelCanvas:
    """A pixel framebuffer that renders to Rich Text via half-block characters.

    Each terminal cell represents 2 vertical pixels. The image uses Pillow's
    palette mode ('P') where each pixel stores a 0-15 palette index.
    """

    def __init__(
        self,
        width: int,
        height: int,
        fill: int = 0,
        scanlines: bool = False,
    ) -> None:
        self.width = width
        self.height = height
        self._fill = fill
        self.scanlines = scanlines
        self.image = self._create_image()

    def _create_image(self) -> Image.Image:
        img = Image.new("P", (self.width, self.height), self._fill)
        pal = [0] * 768
        for i, (r, g, b) in enumerate(PALETTE_RGB):
            pal[i * 3] = r
            pal[i * 3 + 1] = g
            pal[i * 3 + 2] = b
        img.putpalette(pal)
        return img

    def clear(self) -> None:
        """Reset all pixels to the fill color."""
        self.image = self._create_image()

    def render(self, cycle: CyclePalette) -> Text:
        """Convert the pixel buffer to a Rich Text using half-block characters.

        Processes pixel rows in pairs (top, bottom). Each pair becomes one
        terminal row. Uses CyclePalette for current color mapping.
        """
        px = self.image.load()
        text = Text()
        rows = (self.height + 1) // 2

        for row in range(rows):
            y_top = row * 2
            y_bot = row * 2 + 1
            has_bot = y_bot < self.height

            for x in range(self.width):
                top_idx = px[x, y_top]
                bot_idx = px[x, y_bot] if has_bot else top_idx

                if self.scanlines:
                    top_rgb = (
                        cycle.get_rgb_darkened(top_idx, _SCANLINE_FACTOR)
                        if y_top % 2 == 1
                        else cycle.get_rgb(top_idx)
                    )
                    bot_rgb = (
                        cycle.get_rgb_darkened(bot_idx, _SCANLINE_FACTOR)
                        if y_bot % 2 == 1
                        else cycle.get_rgb(bot_idx)
                    )
                else:
                    top_rgb = cycle.get_rgb(top_idx)
                    bot_rgb = cycle.get_rgb(bot_idx)

                top_hex = f"#{top_rgb[0]:02x}{top_rgb[1]:02x}{top_rgb[2]:02x}"
                bot_hex = f"#{bot_rgb[0]:02x}{bot_rgb[1]:02x}{bot_rgb[2]:02x}"

                if top_hex == bot_hex:
                    style = Style(bgcolor=top_hex)
                    text.append(_SPACE, style=style)
                else:
                    style = Style(color=top_hex, bgcolor=bot_hex)
                    text.append(_UPPER_HALF, style=style)

            if row < rows - 1:
                text.append("\n")

        return text
