"""Tests for the PC-98 coffee scene compositor."""

from rich.text import Text

from digital_caffeine.pc98.scene import CoffeeScene
from digital_caffeine.pc98.sprites import SCENE_W, SCENE_H


class TestCoffeeScene:
    def test_initial_dimensions(self):
        scene = CoffeeScene()
        assert scene.canvas.width == SCENE_W
        assert scene.canvas.height == SCENE_H

    def test_update_increments_frame(self):
        scene = CoffeeScene()
        assert scene.frame == 0
        scene.update()
        assert scene.frame == 1

    def test_render_returns_rich_text(self):
        scene = CoffeeScene()
        scene.update()
        result = scene.render()
        assert isinstance(result, Text)

    def test_render_has_correct_line_count(self):
        scene = CoffeeScene()
        scene.update()
        result = scene.render()
        lines = str(result).split("\n")
        expected_rows = (SCENE_H + 1) // 2
        assert len(lines) == expected_rows

    def test_multiple_updates_dont_crash(self):
        scene = CoffeeScene()
        for _ in range(100):
            scene.update()
        result = scene.render()
        assert isinstance(result, Text)

    def test_animated_surface_changes(self):
        scene = CoffeeScene()
        scene.update()
        r1 = scene.render()
        for _ in range(20):
            scene.update()
        r2 = scene.render()
        assert isinstance(r2, Text)
