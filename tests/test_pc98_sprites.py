"""Tests for PC-98 pixel art sprite drawing functions."""

from PIL import Image

from digital_caffeine.pc98.palette import (
    BLACK,
    DARK_BROWN,
    DEEP_NAVY,
    LIGHT_GRAY,
    PALETTE_RGB,
    SLATE,
    WARM_BROWN,
    WARM_GRAY,
)
from digital_caffeine.pc98.sprites import (
    _CUP_BOTTOM,
    _CUP_RIM_LEFT,
    _CUP_RIM_RIGHT,
    _CUP_TOP,
    _HDL_OUTER_X,
    _HDL_TOP,
    _SAU_LEFT,
    _SAU_TOP,
    SCENE_H,
    SCENE_W,
    draw_background,
    draw_cup,
    draw_handle,
    draw_saucer,
    draw_table,
)


def _make_scene() -> Image.Image:
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
        for y in range(SCENE_H):
            for x in range(SCENE_W):
                assert px[x, y] in (BLACK, DEEP_NAVY, SLATE)

    def test_mostly_deep_navy(self):
        img = _make_scene()
        draw_background(img)
        px = img.load()
        navy = sum(1 for y in range(SCENE_H) for x in range(SCENE_W)
                   if px[x, y] == DEEP_NAVY)
        assert navy > (SCENE_W * SCENE_H * 0.9)


class TestDrawTable:
    def test_table_in_lower_region(self):
        img = _make_scene()
        draw_background(img)
        draw_table(img)
        px = img.load()
        table_colors = (WARM_GRAY, WARM_BROWN, DARK_BROWN, LIGHT_GRAY)
        assert px[SCENE_W // 2, SCENE_H - 1] in table_colors


class TestDrawCup:
    def test_cup_has_outline(self):
        img = _make_scene()
        draw_background(img)
        draw_cup(img)
        px = img.load()
        has_black = any(
            px[x, _CUP_TOP] == BLACK
            for x in range(_CUP_RIM_LEFT, _CUP_RIM_RIGHT + 1)
        )
        assert has_black

    def test_cup_has_coffee_fill(self):
        img = _make_scene()
        draw_background(img)
        draw_cup(img)
        px = img.load()
        coffee_colors = {2, 3, 4, 5, 6, 7}
        mid_y = (_CUP_TOP + _CUP_BOTTOM) // 2
        found = any(
            px[x, mid_y] in coffee_colors
            for x in range(_CUP_RIM_LEFT + 3, _CUP_RIM_RIGHT - 3)
        )
        assert found


class TestDrawSaucer:
    def test_saucer_present(self):
        img = _make_scene()
        draw_background(img)
        draw_saucer(img)
        px = img.load()
        from digital_caffeine.pc98.palette import OFF_WHITE
        saucer_colors = {SLATE, LIGHT_GRAY, BLACK, OFF_WHITE}
        assert px[_SAU_LEFT + 1, _SAU_TOP + 1] in saucer_colors


class TestDrawHandle:
    def test_handle_present(self):
        img = _make_scene()
        draw_background(img)
        draw_handle(img)
        px = img.load()
        from digital_caffeine.pc98.palette import OFF_WHITE
        handle_colors = {WARM_GRAY, LIGHT_GRAY, OFF_WHITE, BLACK}
        assert px[_HDL_OUTER_X, (_HDL_TOP + 40) // 2] in handle_colors
