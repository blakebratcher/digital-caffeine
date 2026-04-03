"""Scene compositor: assembles all PC-98 pixel art layers into a renderable frame."""

from __future__ import annotations

from rich.text import Text

from digital_caffeine.pc98.canvas import PixelCanvas
from digital_caffeine.pc98.palette import AMBER, CREAM, GOLD, OFF_WHITE, CyclePalette
from digital_caffeine.pc98.particles import DripSystem, SteamSystem
from digital_caffeine.pc98.sprites import (
    _CUP_BOTTOM,
    _CUP_TOP,
    _INT_LEFT,
    _INT_RIGHT,
    SCENE_H,
    SCENE_W,
    draw_background,
    draw_cup,
    draw_handle,
    draw_saucer,
    draw_table,
)

_SURFACE_Y_TOP = _CUP_TOP + 2
_SURFACE_Y_BOT = _CUP_TOP + 5  # 3 rows of animated surface (was 2)


class CoffeeScene:
    """Manages the full pixel art scene with all animated elements."""

    def __init__(self) -> None:
        self.canvas = PixelCanvas(SCENE_W, SCENE_H, fill=0, scanlines=True)
        self.cycle = CyclePalette()
        self.frame = 0
        self._steam = SteamSystem(
            count=12,  # more particles for richer steam
            spawn_y=float(_CUP_TOP - 1),
            x_center=(_INT_LEFT + _INT_RIGHT) // 2,
        )
        self._drips = DripSystem(
            spawn_y=_CUP_BOTTOM + 5,
            x_min=_INT_LEFT,
            x_max=_INT_RIGHT,
        )
        self._draw_static()

    def _draw_static(self) -> None:
        draw_background(self.canvas.image)
        draw_table(self.canvas.image)
        draw_cup(self.canvas.image)
        draw_handle(self.canvas.image)
        draw_saucer(self.canvas.image)
        self._static = self.canvas.image.copy()

    def update(self) -> None:
        self.frame += 1
        self.cycle.advance()
        self._steam.update()
        self._drips.update()

        self.canvas.image.paste(self._static)
        px = self.canvas.image.load()

        # Animate coffee surface - rippling colors with highlights
        shimmer_seed = self.frame * 17 + 7
        surface_colors = [AMBER, GOLD, CREAM]
        for y in range(_SURFACE_Y_TOP, _SURFACE_Y_BOT):
            for x in range(_INT_LEFT, _INT_RIGHT + 1):
                phase = (x + self.frame // 3 + y * 2) % 3
                px[x, y] = surface_colors[phase]

        # Bright shimmer highlights that travel across the surface
        for i in range(4):
            sx = _INT_LEFT + (
                (shimmer_seed + i * 7 + self.frame // 2) % (_INT_RIGHT - _INT_LEFT)
            )
            sy = _SURFACE_Y_TOP + (i % (_SURFACE_Y_BOT - _SURFACE_Y_TOP))
            if _INT_LEFT <= sx <= _INT_RIGHT:
                px[sx, sy] = OFF_WHITE

        # Draw steam (only on background pixels - don't overwrite cup/table)
        bg_colors = {0, 1}  # BLACK, DEEP_NAVY
        for x, y, ci in self._steam.get_draw_list():
            if 0 <= x < SCENE_W and 0 <= y < SCENE_H:
                if px[x, y] in bg_colors:
                    px[x, y] = ci

        # Draw drips
        for x, y, ci in self._drips.get_draw_list():
            if 0 <= x < SCENE_W and 0 <= y < SCENE_H:
                px[x, y] = ci

    def render(self) -> Text:
        return self.canvas.render(self.cycle)
