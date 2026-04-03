"""Tests for the PC-98 16-color palette and cycling logic."""

from digital_caffeine.pc98.palette import (
    PALETTE,
    PALETTE_RGB,
    CyclePalette,
    dither_pick,
)


class TestPaletteConstants:
    def test_palette_has_16_colors(self):
        assert len(PALETTE) == 16

    def test_palette_entries_are_hex(self):
        for color in PALETTE:
            assert color.startswith("#")
            assert len(color) == 7

    def test_palette_rgb_has_16_entries(self):
        assert len(PALETTE_RGB) == 16

    def test_palette_rgb_values_in_range(self):
        for r, g, b in PALETTE_RGB:
            assert 0 <= r <= 255
            assert 0 <= g <= 255
            assert 0 <= b <= 255

    def test_palette_rgb_matches_hex(self):
        for hex_color, (r, g, b) in zip(PALETTE, PALETTE_RGB):
            assert r == int(hex_color[1:3], 16)
            assert g == int(hex_color[3:5], 16)
            assert b == int(hex_color[5:7], 16)


class TestCyclePalette:
    def test_initial_state_matches_base(self):
        cp = CyclePalette()
        for i in range(16):
            assert cp.get_rgb(i) == PALETTE_RGB[i]

    def test_advance_changes_cycling_indices(self):
        cp = CyclePalette()
        original_5 = cp.get_rgb(5)
        # Advance coffee cycle (indices 5,6,7 rotate every 4 frames)
        for _ in range(4):
            cp.advance()
        # After one rotation step, index 5 should now map to what was 6
        assert cp.get_rgb(5) == PALETTE_RGB[6]

    def test_non_cycling_indices_unchanged(self):
        cp = CyclePalette()
        original_0 = cp.get_rgb(0)
        original_3 = cp.get_rgb(3)
        for _ in range(100):
            cp.advance()
        assert cp.get_rgb(0) == original_0
        assert cp.get_rgb(3) == original_3

    def test_coffee_cycle_wraps(self):
        cp = CyclePalette()
        # 3 steps of 4 frames = 12 frames, coffee cycle has 3 indices
        for _ in range(12):
            cp.advance()
        # Should be back to original
        assert cp.get_rgb(5) == PALETTE_RGB[5]

    def test_get_hex(self):
        cp = CyclePalette()
        hex_color = cp.get_hex(0)
        assert hex_color == "#000000"

    def test_build_pillow_palette(self):
        cp = CyclePalette()
        pal = cp.build_pillow_palette()
        assert len(pal) == 768  # 256 * 3
        # First color is black
        assert pal[0:3] == [0, 0, 0]

    def test_darken_for_scanlines(self):
        cp = CyclePalette()
        normal = cp.get_rgb(15)  # off-white
        dark = cp.get_rgb_darkened(15, 0.8)
        assert dark[0] < normal[0]
        assert dark[1] < normal[1]
        assert dark[2] < normal[2]


class TestDitherPick:
    def test_same_color_returns_that_color(self):
        assert dither_pick(3, 3, 0, 0) == 3

    def test_dither_is_deterministic(self):
        a = dither_pick(2, 3, 5, 7)
        b = dither_pick(2, 3, 5, 7)
        assert a == b

    def test_dither_returns_one_of_two_colors(self):
        results = set()
        for x in range(4):
            for y in range(4):
                results.add(dither_pick(2, 3, x, y))
        assert results == {2, 3}

    def test_dither_roughly_balanced(self):
        count_a = sum(
            1 for x in range(8) for y in range(8) if dither_pick(0, 1, x, y) == 0
        )
        # 2x2 ordered dither should give ~50% split
        assert 20 <= count_a <= 44
