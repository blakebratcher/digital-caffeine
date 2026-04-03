"""Scene compositor: assembles all PC-98 pixel art layers into a renderable frame."""

from __future__ import annotations

from rich.text import Text

from digital_caffeine.pc98.canvas import PixelCanvas
from digital_caffeine.pc98.palette import AMBER, CREAM, GOLD, OFF_WHITE, CyclePalette
from digital_caffeine.pc98.particles import DripSystem, SteamSystem
from digital_caffeine.pc98.sprites import (
    _CUP_BOTTOM,
    _CUP_RIM_LEFT,
    _CUP_RIM_RIGHT,
    _CUP_TOP,
    _INT_LEFT,
    _INT_RIGHT,
    _PILLAR_W,
    SCENE_H,
    SCENE_W,
    draw_background,
    draw_cup,
    draw_handle,
    draw_ornate_pillars,
    draw_saucer,
    draw_table,
    draw_window,
)

_SURFACE_Y_TOP = _CUP_TOP + 2
_SURFACE_Y_BOT = _CUP_TOP + 5

# Colors that steam can draw over
_STEAM_BG = frozenset({0, 1, 11, 12})  # BLACK, DEEP_NAVY, STEEL_BLUE, SLATE


class CoffeeScene:
    """Manages the full pixel art scene with all animated elements."""

    def __init__(self) -> None:
        self.canvas = PixelCanvas(SCENE_W, SCENE_H, fill=0, scanlines=True)
        self.cycle = CyclePalette()
        self.frame = 0
        cup_cx = (_CUP_RIM_LEFT + _CUP_RIM_RIGHT) // 2
        self._steam = SteamSystem(
            count=10,
            spawn_y=float(_CUP_TOP - 1),
            x_center=cup_cx,
        )
        self._drips = DripSystem(
            spawn_y=_CUP_BOTTOM + 3,
            x_min=_INT_LEFT,
            x_max=_INT_RIGHT,
        )
        self._draw_static()

    def _draw_static(self) -> None:
        draw_background(self.canvas.image)
        draw_window(self.canvas.image)
        draw_table(self.canvas.image)
        draw_cup(self.canvas.image)
        draw_handle(self.canvas.image)
        draw_saucer(self.canvas.image)
        draw_ornate_pillars(self.canvas.image)
        self._static = self.canvas.image.copy()

    def update(self) -> None:
        self.frame += 1
        self.cycle.advance()
        self._steam.update()
        self._drips.update()

        self.canvas.image.paste(self._static)
        px = self.canvas.image.load()

        # Animate coffee surface - clean ripple
        surface_colors = [AMBER, GOLD, CREAM]
        for y in range(_SURFACE_Y_TOP, _SURFACE_Y_BOT):
            # Compute tapered width for this row
            cup_h = _CUP_BOTTOM - _CUP_TOP
            t = (y - _CUP_TOP) / max(1, cup_h)
            from digital_caffeine.pc98.sprites import (
                _CUP_BASE_LEFT,
                _CUP_BASE_RIGHT,
            )
            left = int(_CUP_RIM_LEFT + t * (_CUP_BASE_LEFT - _CUP_RIM_LEFT)) + 2
            right = int(_CUP_RIM_RIGHT - t * (_CUP_RIM_RIGHT - _CUP_BASE_RIGHT)) - 2
            for x in range(left, right + 1):
                phase = (x + self.frame // 3) % 3
                px[x, y] = surface_colors[phase]

        # Shimmer highlight
        seed = self.frame * 17 + 7
        for i in range(3):
            sx = _INT_LEFT + (seed + i * 7) % max(1, _INT_RIGHT - _INT_LEFT)
            if _SURFACE_Y_TOP <= _SURFACE_Y_TOP + (i % 3) < _SURFACE_Y_BOT:
                if _INT_LEFT <= sx <= _INT_RIGHT:
                    px[sx, _SURFACE_Y_TOP + (i % 3)] = OFF_WHITE

        # Steam: draws over background and window, not over cup/table/pillars
        pr = _PILLAR_W
        pl = SCENE_W - _PILLAR_W
        for x, y, ci in self._steam.get_draw_list():
            if pr <= x < pl and 0 <= y < SCENE_H:
                if px[x, y] in _STEAM_BG:
                    px[x, y] = ci

        # Drips
        for x, y, ci in self._drips.get_draw_list():
            if pr <= x < pl and 0 <= y < SCENE_H:
                px[x, y] = ci

    def render(self) -> Text:
        return self.canvas.render(self.cycle)
