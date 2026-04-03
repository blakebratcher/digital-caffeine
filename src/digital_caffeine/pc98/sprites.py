"""PC-98 pixel art sprite drawing functions.

All functions draw onto a Pillow palette-mode Image using palette indices.
Coordinate system: (0,0) is top-left. Scene is SCENE_W x SCENE_H pixels.
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

# Scene dimensions - larger for denser pixel art
SCENE_W = 80
SCENE_H = 96

# -- Layout constants ---------------------------------------------------------

_PILLAR_W = 6

# Cup body - centered between pillars
_CUP_LEFT = 21
_CUP_RIGHT = 58
_CUP_TOP = 34
_CUP_BOTTOM = 72
_CUP_WALL = 2

# Cup interior
_INT_LEFT = _CUP_LEFT + _CUP_WALL
_INT_RIGHT = _CUP_RIGHT - _CUP_WALL
_INT_TOP = _CUP_TOP + 3

# Coffee fill layers
_CREMA_TOP = _INT_TOP
_CREMA_BOT = _INT_TOP + 4
_LIGHT_TOP = _CREMA_BOT
_LIGHT_BOT = _LIGHT_TOP + 6
_MED_TOP = _LIGHT_BOT
_MED_BOT = _MED_TOP + 8
_DARK_TOP = _MED_BOT
_DARK_BOT = _DARK_TOP + 8
_DEEP_TOP = _DARK_BOT
_DEEP_BOT = _CUP_BOTTOM - _CUP_WALL

# Handle
_HDL_LEFT = _CUP_RIGHT + 1
_HDL_RIGHT = _CUP_RIGHT + 9
_HDL_TOP = _CUP_TOP + 7
_HDL_BOT = _CUP_BOTTOM - 8

# Saucer
_SAU_LEFT = 15
_SAU_RIGHT = 64
_SAU_TOP = 73
_SAU_BOT = 78

# Table
_TABLE_TOP = 78

# Window
_WIN_LEFT = _PILLAR_W + 6
_WIN_RIGHT = SCENE_W - _PILLAR_W - 6
_WIN_TOP = 3
_WIN_BOT = 28


def draw_background(img: Image.Image) -> None:
    """Fill with deep navy and subtle ambient light gradient."""
    draw = ImageDraw.Draw(img)
    px = img.load()
    draw.rectangle([0, 0, SCENE_W - 1, SCENE_H - 1], fill=DEEP_NAVY)

    # Subtle ambient glow in the center-top (from window light)
    for y in range(_WIN_BOT + 1, _CUP_TOP):
        for x in range(_PILLAR_W + 1, SCENE_W - _PILLAR_W - 1):
            cx = SCENE_W // 2
            dist = abs(x - cx)
            if dist < 15 and (x + y) % 7 == 0:
                px[x, y] = SLATE


def draw_ornate_pillars(img: Image.Image) -> None:
    """Draw ornate PC-98 style decorative pillar borders."""
    px = img.load()

    for side in (0, 1):
        x0 = 0 if side == 0 else SCENE_W - _PILLAR_W

        # Base fill with rich dithered texture
        for y in range(SCENE_H):
            for x in range(x0, x0 + _PILLAR_W):
                if x == x0 or x == x0 + _PILLAR_W - 1:
                    px[x, y] = BLACK  # outer/inner edge
                elif x == (x0 + 1 if side == 0 else x0 + _PILLAR_W - 2):
                    px[x, y] = DARK_BROWN  # shadow edge
                else:
                    px[x, y] = dither_pick(WARM_BROWN, CHOCOLATE, x, y)

        # Inner highlight edge
        hx = x0 + _PILLAR_W - 1 if side == 0 else x0
        for y in range(SCENE_H):
            px[hx, y] = WARM_GRAY

        # Ornate gem diamonds every 8 pixels
        mid_x = x0 + _PILLAR_W // 2
        for gy in range(4, SCENE_H - 4, 8):
            # Diamond: 3x3 with center bright
            px[mid_x, gy] = MAGENTA
            for dy in (-1, 1):
                if 0 <= gy + dy < SCENE_H:
                    px[mid_x, gy + dy] = DUSTY_ROSE
            for dx in (-1, 1):
                nx = mid_x + dx
                if x0 + 1 <= nx < x0 + _PILLAR_W - 1:
                    px[nx, gy] = DUSTY_ROSE

        # Horizontal ornate bands every 16 pixels
        for by in range(0, SCENE_H, 16):
            for x in range(x0 + 1, x0 + _PILLAR_W - 1):
                px[x, by] = DEEP_RED
                if by + 1 < SCENE_H:
                    px[x, by + 1] = MAGENTA
                if by + 2 < SCENE_H:
                    px[x, by + 2] = DEEP_RED

        # Vertical groove lines for depth
        gx = x0 + 2 if side == 0 else x0 + _PILLAR_W - 3
        for y in range(SCENE_H):
            if y % 16 > 2:  # skip the horizontal bands
                px[gx, y] = DARK_BROWN


def draw_window(img: Image.Image) -> None:
    """Draw a detailed window with curtains and light."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Window frame - thick, warm
    draw.rectangle([_WIN_LEFT, _WIN_TOP, _WIN_RIGHT, _WIN_BOT],
                    fill=WARM_GRAY)
    draw.rectangle([_WIN_LEFT, _WIN_TOP, _WIN_RIGHT, _WIN_BOT],
                    outline=BLACK)
    draw.rectangle([_WIN_LEFT + 1, _WIN_TOP + 1, _WIN_RIGHT - 1, _WIN_BOT - 1],
                    outline=LIGHT_GRAY)

    # Window pane - deep blue sky
    pane_l = _WIN_LEFT + 2
    pane_r = _WIN_RIGHT - 2
    pane_t = _WIN_TOP + 2
    pane_b = _WIN_BOT - 2
    draw.rectangle([pane_l, pane_t, pane_r, pane_b], fill=STEEL_BLUE)

    # Crossbars
    mid_x = (_WIN_LEFT + _WIN_RIGHT) // 2
    mid_y = (_WIN_TOP + _WIN_BOT) // 2
    draw.line([(mid_x, pane_t), (mid_x, pane_b)], fill=WARM_GRAY)
    draw.line([(pane_l, mid_y), (pane_r, mid_y)], fill=WARM_GRAY)
    # Crossbar highlight
    draw.line([(mid_x + 1, pane_t), (mid_x + 1, pane_b)], fill=LIGHT_GRAY)
    draw.line([(pane_l, mid_y + 1), (pane_r, mid_y + 1)], fill=LIGHT_GRAY)

    # Stars/light through the window panes
    stars = [(pane_l + 4, pane_t + 3), (pane_r - 5, pane_t + 4),
             (pane_l + 8, pane_b - 4), (pane_r - 8, pane_b - 3),
             (mid_x + 5, pane_t + 5), (mid_x - 6, pane_b - 5)]
    for sx, sy in stars:
        if pane_l < sx < pane_r and pane_t < sy < pane_b:
            px[sx, sy] = OFF_WHITE

    # Curtains on both sides - rich deep red with folds
    curtain_w = 4
    for cy in range(pane_t, pane_b + 1):
        # Left curtain
        for cx in range(pane_l, pane_l + curtain_w):
            fold = (cy + cx) % 3
            if fold == 0:
                px[cx, cy] = DEEP_RED
            elif fold == 1:
                px[cx, cy] = MAGENTA
            else:
                px[cx, cy] = DARK_BROWN
        # Right curtain
        for cx in range(pane_r - curtain_w + 1, pane_r + 1):
            fold = (cy + cx) % 3
            if fold == 0:
                px[cx, cy] = DEEP_RED
            elif fold == 1:
                px[cx, cy] = MAGENTA
            else:
                px[cx, cy] = DARK_BROWN

    # Window sill
    draw.line([(_WIN_LEFT, _WIN_BOT + 1), (_WIN_RIGHT, _WIN_BOT + 1)],
              fill=LIGHT_GRAY)
    draw.line([(_WIN_LEFT, _WIN_BOT + 2), (_WIN_RIGHT, _WIN_BOT + 2)],
              fill=WARM_GRAY)


def draw_shelf(img: Image.Image) -> None:
    """Draw a small decorative shelf on the wall beside the window."""
    px = img.load()
    draw = ImageDraw.Draw(img)

    # Shelf on the right side between window and pillar
    sx0 = _WIN_RIGHT + 3
    sx1 = SCENE_W - _PILLAR_W - 2
    sy = _WIN_BOT - 5

    if sx1 <= sx0:
        return

    # Shelf board
    draw.line([(sx0, sy), (sx1, sy)], fill=WARM_BROWN)
    draw.line([(sx0, sy + 1), (sx1, sy + 1)], fill=DARK_BROWN)

    # Small bottle/jar on shelf
    bx = (sx0 + sx1) // 2
    for by in range(sy - 4, sy):
        px[bx, by] = DUSTY_ROSE
        if bx + 1 <= sx1:
            px[bx + 1, by] = MAGENTA
    # Bottle cap
    if sy - 5 >= 0:
        px[bx, sy - 5] = WARM_GRAY


def draw_table(img: Image.Image) -> None:
    """Draw a detailed wooden table surface."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    t_left = _PILLAR_W
    t_right = SCENE_W - _PILLAR_W - 1

    # Table edge with depth
    draw.line([(t_left, _TABLE_TOP), (t_right, _TABLE_TOP)], fill=CREAM)
    draw.line([(t_left, _TABLE_TOP + 1), (t_right, _TABLE_TOP + 1)],
              fill=LIGHT_GRAY)

    # Table body
    for y in range(_TABLE_TOP + 2, SCENE_H):
        for x in range(t_left, t_right + 1):
            band = (y - _TABLE_TOP) // 3
            if band % 2 == 0:
                px[x, y] = WARM_GRAY
            else:
                px[x, y] = WARM_BROWN
            # Grain variation
            if (x * 7 + y * 13) % 31 == 0:
                px[x, y] = DARK_BROWN
            elif (x * 11 + y * 3) % 37 == 0:
                px[x, y] = LIGHT_GRAY

    # Grain lines
    for y in range(_TABLE_TOP + 2, SCENE_H, 4):
        for x in range(t_left, t_right + 1):
            px[x, y] = dither_pick(LIGHT_GRAY, WARM_GRAY, x, y)


def draw_cup(img: Image.Image) -> None:
    """Draw a detailed coffee cup with PC-98 style shading and highlights."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # -- Outer shape with thick outline --
    draw.rectangle([_CUP_LEFT, _CUP_TOP, _CUP_RIGHT, _CUP_BOTTOM],
                    outline=BLACK)
    # Second outline for thickness
    draw.rectangle([_CUP_LEFT + 1, _CUP_TOP + 1,
                     _CUP_RIGHT - 1, _CUP_BOTTOM - 1],
                    outline=BLACK)

    # -- Cup body walls with lighting gradient --
    # Left wall: bright (light source from upper-left)
    for y in range(_CUP_TOP + 2, _CUP_BOTTOM - 1):
        px[_CUP_LEFT + 2, y] = OFF_WHITE
        px[_CUP_LEFT + 3, y] = LIGHT_GRAY

    # Right wall: darker, more muted
    for y in range(_CUP_TOP + 2, _CUP_BOTTOM - 1):
        px[_CUP_RIGHT - 2, y] = WARM_GRAY
        px[_CUP_RIGHT - 3, y] = LIGHT_GRAY

    # -- Rim: 3px thick, the crown of the cup --
    for x in range(_CUP_LEFT + 2, _CUP_RIGHT - 1):
        px[x, _CUP_TOP + 2] = OFF_WHITE  # top bright line
        px[x, _CUP_TOP + 3] = LIGHT_GRAY  # middle
        px[x, _CUP_TOP + 4] = WARM_GRAY   # bottom shadow

    # Rim PC-98 rose/magenta accent highlights
    for x in range(_CUP_LEFT + 3, _CUP_RIGHT - 2):
        if x % 3 == 0:
            px[x, _CUP_TOP + 2] = DUSTY_ROSE
        if x % 5 == 0:
            px[x, _CUP_TOP + 3] = MAGENTA

    # -- Cup bottom --
    for x in range(_CUP_LEFT + 2, _CUP_RIGHT - 1):
        px[x, _CUP_BOTTOM - 2] = WARM_GRAY
        px[x, _CUP_BOTTOM - 3] = LIGHT_GRAY

    # -- Coffee fill with rich layered gradient --
    _fill_layer(px, _CREMA_TOP, _CREMA_BOT, CREAM, AMBER)
    _fill_layer(px, _LIGHT_TOP, _LIGHT_BOT, CHOCOLATE, AMBER)
    _fill_layer(px, _MED_TOP, _MED_BOT, WARM_BROWN, CHOCOLATE)
    _fill_layer(px, _DARK_TOP, _DARK_BOT, DARK_BROWN, WARM_BROWN)
    _fill_layer(px, _DEEP_TOP, _DEEP_BOT, DARK_BROWN, DARK_BROWN)

    # Dithered transitions
    for x in range(_INT_LEFT, _INT_RIGHT + 1):
        for boundary, c1, c2 in [
            (_CREMA_BOT, AMBER, CHOCOLATE),
            (_LIGHT_BOT, CHOCOLATE, WARM_BROWN),
            (_MED_BOT, WARM_BROWN, DARK_BROWN),
        ]:
            if boundary < SCENE_H:
                px[x, boundary] = dither_pick(c1, c2, x, boundary)
                if boundary + 1 < SCENE_H:
                    px[x, boundary + 1] = dither_pick(c2, c1, x, boundary + 1)

    # -- Specular highlights on crema --
    for y in range(_CREMA_TOP, min(_CREMA_TOP + 3, _CREMA_BOT)):
        px[_INT_LEFT, y] = OFF_WHITE
        px[_INT_LEFT + 1, y] = OFF_WHITE
        px[_INT_LEFT + 2, y] = GOLD

    # Warm glow reflected on left cup wall from coffee
    for y in range(_CREMA_TOP, _MED_TOP):
        px[_CUP_LEFT + 2, y] = dither_pick(OFF_WHITE, AMBER, _CUP_LEFT, y)
        px[_CUP_LEFT + 3, y] = dither_pick(LIGHT_GRAY, GOLD, _CUP_LEFT, y)


def _fill_layer(
    px: object,
    y_top: int,
    y_bot: int,
    primary: int,
    accent: int,
) -> None:
    """Fill a coffee layer with rich dithered texture."""
    for y in range(y_top, y_bot):
        for x in range(_INT_LEFT, _INT_RIGHT + 1):
            # More complex dither - creates a richer texture
            h = (x * 7 + y * 13) % 20
            if h < 3:
                px[x, y] = accent
            elif h < 5:
                px[x, y] = dither_pick(primary, accent, x, y)
            else:
                px[x, y] = primary


def draw_handle(img: Image.Image) -> None:
    """Draw a detailed cup handle with shading."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Outer outline
    draw.rectangle([_HDL_LEFT, _HDL_TOP, _HDL_RIGHT, _HDL_BOT],
                    outline=BLACK)
    draw.rectangle([_HDL_LEFT + 1, _HDL_TOP + 1,
                     _HDL_RIGHT - 1, _HDL_BOT - 1],
                    outline=BLACK)

    # Fill
    for y in range(_HDL_TOP + 2, _HDL_BOT - 1):
        for x in range(_HDL_LEFT + 2, _HDL_RIGHT - 1):
            px[x, y] = WARM_GRAY

    # Top highlight
    for x in range(_HDL_LEFT + 2, _HDL_RIGHT - 1):
        px[x, _HDL_TOP + 2] = OFF_WHITE
        px[x, _HDL_TOP + 3] = LIGHT_GRAY

    # Left edge (connects to cup)
    for y in range(_HDL_TOP + 2, _HDL_BOT - 1):
        px[_HDL_LEFT + 2, y] = LIGHT_GRAY

    # Hollow interior
    il = _HDL_LEFT + 4
    ir = _HDL_RIGHT - 2
    it = _HDL_TOP + 5
    ib = _HDL_BOT - 4
    if ir > il and ib > it:
        draw.rectangle([il, it, ir, ib], fill=DEEP_NAVY)
        draw.rectangle([il, it, ir, ib], outline=BLACK)
        # Inner shadow
        for y in range(it + 1, ib):
            px[il + 1, y] = SLATE


def draw_saucer(img: Image.Image) -> None:
    """Draw a detailed saucer with rim highlights and depth."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Main body
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], fill=SLATE)
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], outline=BLACK)

    # Top rim - bright, catches light
    for x in range(_SAU_LEFT + 1, _SAU_RIGHT):
        px[x, _SAU_TOP + 1] = LIGHT_GRAY
        px[x, _SAU_TOP + 2] = OFF_WHITE
        if x % 4 == 0:
            px[x, _SAU_TOP + 2] = DUSTY_ROSE

    # Bottom shadow
    for x in range(_SAU_LEFT + 1, _SAU_RIGHT):
        px[x, _SAU_BOT - 1] = DARK_BROWN

    # Saucer inner detail
    for y in range(_SAU_TOP + 3, _SAU_BOT - 1):
        for x in range(_SAU_LEFT + 1, _SAU_RIGHT):
            if (x + y) % 5 == 0:
                px[x, y] = WARM_GRAY

    # Shadow on table below saucer
    shadow_y = max(_SAU_BOT + 1, _TABLE_TOP)
    for y in range(shadow_y, min(shadow_y + 3, SCENE_H)):
        for x in range(_SAU_LEFT + 3, _SAU_RIGHT - 2):
            if _PILLAR_W <= x < SCENE_W - _PILLAR_W:
                px[x, y] = DARK_BROWN
