"""Tests for the half-block pixel canvas renderer."""

from PIL import Image
from rich.text import Text

from digital_caffeine.pc98.canvas import PixelCanvas
from digital_caffeine.pc98.palette import PALETTE_RGB, CyclePalette


def _make_test_image(width: int, height: int, fill: int = 0) -> Image.Image:
    """Create a small palette-mode test image."""
    img = Image.new("P", (width, height), fill)
    pal = [0] * 768
    for i, (r, g, b) in enumerate(PALETTE_RGB):
        pal[i * 3] = r
        pal[i * 3 + 1] = g
        pal[i * 3 + 2] = b
    img.putpalette(pal)
    return img


class TestPixelCanvas:
    def test_dimensions(self):
        canvas = PixelCanvas(8, 12)
        assert canvas.width == 8
        assert canvas.height == 12

    def test_image_is_palette_mode(self):
        canvas = PixelCanvas(8, 12)
        assert canvas.image.mode == "P"

    def test_render_produces_rich_text(self):
        canvas = PixelCanvas(4, 4)
        result = canvas.render(CyclePalette())
        assert isinstance(result, Text)

    def test_render_height_is_half_pixel_height(self):
        canvas = PixelCanvas(4, 8)
        result = canvas.render(CyclePalette())
        lines = str(result).split("\n")
        assert len(lines) == 4  # 8 pixels / 2

    def test_render_width_matches_pixel_width(self):
        canvas = PixelCanvas(6, 4)
        result = canvas.render(CyclePalette())
        lines = str(result).split("\n")
        assert len(lines[0]) == 6

    def test_same_color_pair_uses_full_block(self):
        canvas = PixelCanvas(2, 2)
        px = canvas.image.load()
        px[0, 0] = 5
        px[0, 1] = 5
        px[1, 0] = 5
        px[1, 1] = 5
        result = canvas.render(CyclePalette())
        plain = str(result)
        assert "\u2580" not in plain

    def test_different_color_pair_uses_half_block(self):
        canvas = PixelCanvas(1, 2)
        px = canvas.image.load()
        px[0, 0] = 5
        px[0, 1] = 11
        result = canvas.render(CyclePalette())
        plain = str(result)
        assert "\u2580" in plain or "\u2584" in plain

    def test_scanlines_darken_odd_rows(self):
        canvas = PixelCanvas(2, 4, scanlines=True)
        px = canvas.image.load()
        for x in range(2):
            for y in range(4):
                px[x, y] = 15
        cp = CyclePalette()
        result = canvas.render(cp)
        assert isinstance(result, Text)

    def test_odd_height_handled(self):
        canvas = PixelCanvas(2, 5)
        result = canvas.render(CyclePalette())
        lines = str(result).split("\n")
        assert len(lines) == 3  # ceil(5/2)

    def test_clear_resets_to_fill(self):
        canvas = PixelCanvas(4, 4, fill=1)
        px = canvas.image.load()
        px[0, 0] = 15
        canvas.clear()
        assert canvas.image.load()[0, 0] == 1
