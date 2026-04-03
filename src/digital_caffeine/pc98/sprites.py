"""PC-98 pixel art sprite drawing functions.

All functions draw onto a Pillow palette-mode Image using palette indices.
Every pixel is placed with purpose - clean outlines, smooth gradients,
readable silhouettes. Light source: upper-left.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from digital_caffeine.pc98.palette import (
    AMBER,
    BLACK,
    CHOCOLATE,
    CREAM,
    DARK_BROWN,
    DEEP_NAVY,
    DEEP_RED,
    DUSTY_ROSE,
    GOLD,
    LIGHT_GRAY,
    MAGENTA,
    OFF_WHITE,
    SLATE,
    STEEL_BLUE,
    WARM_BROWN,
    WARM_GRAY,
    dither_pick,
)

SCENE_W = 56
SCENE_H = 68

# -- Layout -------------------------------------------------------------------

_PILLAR_W = 4

# Cup: slightly tapered (wider rim, narrower base)
_CUP_RIM_LEFT = 14
_CUP_RIM_RIGHT = 40
_CUP_BASE_LEFT = 16
_CUP_BASE_RIGHT = 38
_CUP_TOP = 25
_CUP_BOTTOM = 50

# Interior (inside the 1px walls)
_INT_LEFT = _CUP_RIM_LEFT + 2
_INT_RIGHT = _CUP_RIM_RIGHT - 2
_INT_TOP = _CUP_TOP + 2

# Handle: C-shape extending right
_HDL_OUTER_X = 44
_HDL_TOP = 30
_HDL_BOT = 46
_HDL_MID_TOP = 33
_HDL_MID_BOT = 43

# Saucer
_SAU_LEFT = 10
_SAU_RIGHT = 46
_SAU_TOP = 51
_SAU_BOT = 54

# Table
_TABLE_TOP = 55

# Window
_WIN_LEFT = _PILLAR_W + 3
_WIN_RIGHT = SCENE_W - _PILLAR_W - 3
_WIN_TOP = 2
_WIN_BOT = 19


def draw_background(img: Image.Image) -> None:
    """Solid deep navy background. Calm and quiet."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SCENE_W - 1, SCENE_H - 1], fill=DEEP_NAVY)


def draw_ornate_pillars(img: Image.Image) -> None:
    """Decorative pillar borders on left and right edges."""
    px = img.load()

    for side in (0, 1):
        x0 = 0 if side == 0 else SCENE_W - _PILLAR_W

        for y in range(SCENE_H):
            # Outer edge: black
            px[x0 if side == 0 else x0 + _PILLAR_W - 1, y] = BLACK
            # Inner edge: warm highlight
            px[x0 + _PILLAR_W - 1 if side == 0 else x0, y] = WARM_GRAY
            # Body: clean dither
            for x in range(x0 + 1, x0 + _PILLAR_W - 1):
                px[x, y] = dither_pick(WARM_BROWN, CHOCOLATE, x, y)

        # Gem accents
        mid = x0 + _PILLAR_W // 2
        for gy in range(5, SCENE_H - 3, 10):
            px[mid, gy] = MAGENTA
            if gy - 1 >= 0:
                px[mid, gy - 1] = DUSTY_ROSE
            if gy + 1 < SCENE_H:
                px[mid, gy + 1] = DUSTY_ROSE

        # Horizontal bands
        for by in range(0, SCENE_H, 14):
            for x in range(x0 + 1, x0 + _PILLAR_W - 1):
                px[x, by] = DEEP_RED
                if by + 1 < SCENE_H:
                    px[x, by + 1] = MAGENTA


def draw_window(img: Image.Image) -> None:
    """Window with curtains and night sky."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Frame
    draw.rectangle([_WIN_LEFT, _WIN_TOP, _WIN_RIGHT, _WIN_BOT], outline=WARM_GRAY)
    draw.rectangle([_WIN_LEFT + 1, _WIN_TOP + 1, _WIN_RIGHT - 1, _WIN_BOT - 1],
                    outline=LIGHT_GRAY)

    # Sky pane
    pl, pt = _WIN_LEFT + 2, _WIN_TOP + 2
    pr, pb = _WIN_RIGHT - 2, _WIN_BOT - 2
    draw.rectangle([pl, pt, pr, pb], fill=STEEL_BLUE)

    # Crossbars
    mx = (pl + pr) // 2
    my = (pt + pb) // 2
    for x in range(pl, pr + 1):
        px[x, my] = WARM_GRAY
    for y in range(pt, pb + 1):
        px[mx, y] = WARM_GRAY

    # Stars
    for sx, sy in [(pl + 3, pt + 2), (pr - 4, pt + 3), (mx + 4, pb - 3),
                   (pl + 6, pb - 2), (pr - 6, pt + 5)]:
        if pl < sx < pr and pt < sy < pb and px[sx, sy] == STEEL_BLUE:
            px[sx, sy] = OFF_WHITE

    # Curtains: 2px wide on each side, clean vertical stripes
    for y in range(pt, pb + 1):
        # Left curtain
        px[pl, y] = DEEP_RED
        px[pl + 1, y] = MAGENTA if y % 2 == 0 else DEEP_RED
        # Right curtain
        px[pr, y] = DEEP_RED
        px[pr - 1, y] = MAGENTA if y % 2 == 0 else DEEP_RED

    # Sill
    draw.line([(_WIN_LEFT, _WIN_BOT + 1), (_WIN_RIGHT, _WIN_BOT + 1)],
              fill=LIGHT_GRAY)


def draw_table(img: Image.Image) -> None:
    """Wooden table surface with clean grain."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    tl = _PILLAR_W
    tr = SCENE_W - _PILLAR_W - 1

    # Edge highlight
    draw.line([(tl, _TABLE_TOP), (tr, _TABLE_TOP)], fill=CREAM)
    draw.line([(tl, _TABLE_TOP + 1), (tr, _TABLE_TOP + 1)], fill=LIGHT_GRAY)

    # Body: alternating warm bands
    for y in range(_TABLE_TOP + 2, SCENE_H):
        band = (y - _TABLE_TOP) // 3
        color = WARM_GRAY if band % 2 == 0 else WARM_BROWN
        for x in range(tl, tr + 1):
            px[x, y] = color

    # Clean grain lines
    for y in range(_TABLE_TOP + 4, SCENE_H, 4):
        for x in range(tl, tr + 1):
            px[x, y] = LIGHT_GRAY


def draw_cup(img: Image.Image) -> None:
    """Coffee cup with tapered shape, smooth gradient, clean shading."""
    px = img.load()
    cup_h = _CUP_BOTTOM - _CUP_TOP

    # -- Build the tapered cup shape pixel by pixel --
    for y in range(_CUP_TOP, _CUP_BOTTOM + 1):
        t = (y - _CUP_TOP) / max(1, cup_h)  # 0 at top, 1 at bottom
        # Interpolate between rim width and base width
        left = int(_CUP_RIM_LEFT + t * (_CUP_BASE_LEFT - _CUP_RIM_LEFT))
        right = int(_CUP_RIM_RIGHT - t * (_CUP_RIM_RIGHT - _CUP_BASE_RIGHT))

        # Outline
        px[left, y] = BLACK
        px[right, y] = BLACK

        # Walls
        if left + 1 < right:
            px[left + 1, y] = OFF_WHITE  # lit wall
        if right - 1 > left:
            px[right - 1, y] = WARM_GRAY  # shadow wall

    # Top and bottom edges
    for x in range(_CUP_RIM_LEFT, _CUP_RIM_RIGHT + 1):
        px[x, _CUP_TOP] = BLACK
    for x in range(_CUP_BASE_LEFT, _CUP_BASE_RIGHT + 1):
        px[x, _CUP_BOTTOM] = BLACK

    # -- Rim: bright with rose accents (PC-98 signature) --
    for x in range(_CUP_RIM_LEFT + 1, _CUP_RIM_RIGHT):
        px[x, _CUP_TOP + 1] = OFF_WHITE
        if x % 3 == 0:
            px[x, _CUP_TOP + 1] = DUSTY_ROSE

    # -- Coffee fill: smooth horizontal bands --
    fill_top = _CUP_TOP + 2
    fill_bot = _CUP_BOTTOM - 1
    fill_h = fill_bot - fill_top
    if fill_h <= 0:
        return

    # Layers: (solid_color, start_pct, end_pct)
    # Dithering only at boundaries between layers
    solid_layers = [
        (CREAM, 0.00, 0.10),       # crema
        (AMBER, 0.12, 0.18),       # warm transition
        (CHOCOLATE, 0.20, 0.38),   # light coffee
        (WARM_BROWN, 0.40, 0.58),  # medium
        (DARK_BROWN, 0.60, 0.80),  # dark
        (DARK_BROWN, 0.82, 1.00),  # deepest
    ]
    # Transition rows between layers (dithered)
    transitions = [
        (CREAM, AMBER, 0.10, 0.12),
        (AMBER, CHOCOLATE, 0.18, 0.20),
        (CHOCOLATE, WARM_BROWN, 0.38, 0.40),
        (WARM_BROWN, DARK_BROWN, 0.58, 0.60),
        (DARK_BROWN, DARK_BROWN, 0.80, 0.82),
    ]

    for y in range(fill_top, fill_bot):
        pct = (y - fill_top) / max(1, fill_h)
        t = (y - _CUP_TOP) / max(1, cup_h)
        left = int(_CUP_RIM_LEFT + t * (_CUP_BASE_LEFT - _CUP_RIM_LEFT)) + 2
        right = int(_CUP_RIM_RIGHT - t * (_CUP_RIM_RIGHT - _CUP_BASE_RIGHT)) - 2

        # Check if this row is a transition
        is_trans = False
        for ca, cb, start, end in transitions:
            if start <= pct < end:
                for x in range(left, right + 1):
                    px[x, y] = dither_pick(ca, cb, x, y)
                is_trans = True
                break

        if not is_trans:
            # Solid fill for the layer body
            color = DARK_BROWN  # default
            for sc, start, end in solid_layers:
                if start <= pct < end:
                    color = sc
                    break
            for x in range(left, right + 1):
                px[x, y] = color

    # -- Specular highlight on crema (bright spot upper-left) --
    for dy in range(3):
        y = fill_top + dy
        if y < fill_bot:
            t = (y - _CUP_TOP) / max(1, cup_h)
            left = int(_CUP_RIM_LEFT + t * (_CUP_BASE_LEFT - _CUP_RIM_LEFT)) + 2
            px[left, y] = OFF_WHITE
            if left + 1 <= _INT_RIGHT:
                px[left + 1, y] = GOLD


def draw_handle(img: Image.Image) -> None:
    """C-shaped handle extending from the right side of the cup."""
    px = img.load()

    # The handle is a C-shape: top bar, outer vertical, bottom bar
    # connecting to the cup at _CUP_RIM_RIGHT area

    # Top horizontal bar
    for x in range(_CUP_RIM_RIGHT, _HDL_OUTER_X + 1):
        px[x, _HDL_TOP] = BLACK
        px[x, _HDL_TOP + 1] = OFF_WHITE  # highlight
        px[x, _HDL_TOP + 2] = WARM_GRAY

    # Bottom horizontal bar
    for x in range(_CUP_BASE_RIGHT, _HDL_OUTER_X + 1):
        px[x, _HDL_BOT] = BLACK
        px[x, _HDL_BOT - 1] = WARM_GRAY
        px[x, _HDL_BOT - 2] = LIGHT_GRAY

    # Outer vertical bar
    for y in range(_HDL_TOP, _HDL_BOT + 1):
        px[_HDL_OUTER_X, y] = BLACK
        px[_HDL_OUTER_X - 1, y] = WARM_GRAY
        if _HDL_OUTER_X - 2 > _CUP_RIM_RIGHT:
            px[_HDL_OUTER_X - 2, y] = LIGHT_GRAY

    # Interior of handle (cutout)
    for y in range(_HDL_MID_TOP, _HDL_MID_BOT + 1):
        for x in range(_CUP_RIM_RIGHT + 1, _HDL_OUTER_X - 2):
            if x > 0 and y > 0:
                px[x, y] = DEEP_NAVY


def draw_saucer(img: Image.Image) -> None:
    """Wide saucer plate under the cup with highlights."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Main body
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], fill=SLATE)
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], outline=BLACK)

    # Top highlight
    for x in range(_SAU_LEFT + 1, _SAU_RIGHT):
        px[x, _SAU_TOP + 1] = LIGHT_GRAY
        if x % 5 == 0:
            px[x, _SAU_TOP + 1] = DUSTY_ROSE

    # Shadow below
    for x in range(_SAU_LEFT + 2, _SAU_RIGHT - 1):
        if _SAU_BOT + 1 < SCENE_H:
            px[x, _SAU_BOT + 1] = DARK_BROWN
