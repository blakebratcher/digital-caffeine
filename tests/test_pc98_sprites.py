"""Tests for PC-98 pixel art sprite drawing functions."""

from PIL import Image

from digital_caffeine.pc98.palette import (
    BLACK,
    DARK_BROWN,
    DEEP_NAVY,
    PALETTE_RGB,
    SLATE,
    WARM_BROWN,
    WARM_GRAY,
)
from digital_caffeine.pc98.sprites import (
    SCENE_H,
    SCENE_W,
    draw_background,
    draw_cup,
    draw_handle,
    draw_saucer,
    draw_table,
)


def _make_scene() -> Image.Image:
    """Create a scene image and return it."""
    img = Image.new("P", (SCENE_W, SCENE_H), 0)
    pal = [0] * 768
    for i, (r, g, b) in enumerate(PALETTE_RGB):
        pal[i * 3] = r
        pal[i * 3 + 1] = g
        pal[i * 3 + 2] = b
    img.putpalette(pal)
    return img


class TestDrawBackground:
    def test_fills_entire_image(self):
        img = _make_scene()
        draw_background(img)
        px = img.load()
        # Background is mostly deep navy with sparse star pixels
        for y in range(SCENE_H):
            for x in range(SCENE_W):
                assert px[x, y] in (BLACK, DEEP_NAVY, SLATE)

    def test_mostly_deep_navy(self):
        img = _make_scene()
        draw_background(img)
        px = img.load()
        navy_count = sum(
            1 for y in range(SCENE_H) for x in range(SCENE_W) if px[x, y] == DEEP_NAVY
        )
        # Vast majority should be deep navy
        assert navy_count > (SCENE_W * SCENE_H * 0.9)


class TestDrawTable:
    def test_table_in_lower_region(self):
        img = _make_scene()
        draw_background(img)
        draw_table(img)
        px = img.load()
        from digital_caffeine.pc98.palette import LIGHT_GRAY as LG
        # Table uses warm brown, warm gray, light gray bands
        table_colors = (WARM_GRAY, WARM_BROWN, DARK_BROWN, LG)
        assert px[32, SCENE_H - 1] in table_colors

    def test_table_has_grain_lines(self):
        img = _make_scene()
        draw_background(img)
        draw_table(img)
        px = img.load()
        table_top = 64
        colors_in_table = set()
        for y in range(table_top, SCENE_H):
            colors_in_table.add(px[32, y])
        assert len(colors_in_table) > 1


class TestDrawCup:
    def test_cup_within_scene_bounds(self):
        img = _make_scene()
        draw_background(img)
        draw_cup(img)
        assert img.size == (SCENE_W, SCENE_H)

    def test_cup_has_outline(self):
        img = _make_scene()
        draw_background(img)
        draw_cup(img)
        px = img.load()
        has_black = False
        for x in range(SCENE_W):
            if px[x, 28] == BLACK:
                has_black = True
                break
        assert has_black

    def test_cup_has_coffee_fill(self):
        img = _make_scene()
        draw_background(img)
        draw_cup(img)
        px = img.load()
        coffee_colors = {2, 3, 4, 5, 6, 7}
        found = False
        for x in range(20, 44):
            if px[x, 40] in coffee_colors:
                found = True
                break
        assert found


class TestDrawSaucer:
    def test_saucer_wider_than_cup(self):
        img = _make_scene()
        draw_background(img)
        draw_saucer(img)
        px = img.load()
        from digital_caffeine.pc98.palette import LIGHT_GRAY, SLATE
        saucer_colors = {SLATE, LIGHT_GRAY}
        assert px[14, 60] in saucer_colors


class TestDrawHandle:
    def test_handle_to_right_of_cup(self):
        img = _make_scene()
        draw_background(img)
        draw_handle(img)
        px = img.load()
        from digital_caffeine.pc98.palette import OFF_WHITE
        handle_colors = {WARM_GRAY, OFF_WHITE, BLACK}
        found = False
        for x in range(47, 55):
            if px[x, 40] in handle_colors:
                found = True
                break
        assert found
