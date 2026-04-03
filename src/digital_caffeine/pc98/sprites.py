"""PC-98 pixel art sprite drawing functions.

All functions draw onto a Pillow palette-mode Image using palette indices.
Coordinate system: (0,0) is top-left. Scene is SCENE_W x SCENE_H pixels.
Inspired by the ornate framing and rich detail of PC-98 visual novels.
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
    LIGHT_GRAY,
    MAGENTA,
    OFF_WHITE,
    SLATE,
    STEEL_BLUE,
    WARM_BROWN,
    WARM_GRAY,
    dither_pick,
)

# Scene dimensions (pixels)
SCENE_W = 64
SCENE_H = 80

# -- Layout constants ---------------------------------------------------------

# Ornate border pillars (left and right of the scene)
_PILLAR_W = 5  # width of each decorative pillar

# Cup body (outer edges, including 1px outline) - shifted right for pillars
_CUP_LEFT = 18
_CUP_RIGHT = 47
_CUP_TOP = 28
_CUP_BOTTOM = 58
_CUP_WALL = 2

# Cup interior (inside walls)
_INT_LEFT = _CUP_LEFT + _CUP_WALL
_INT_RIGHT = _CUP_RIGHT - _CUP_WALL
_INT_TOP = _CUP_TOP + 2

# Coffee fill layer boundaries
_CREMA_TOP = _INT_TOP
_CREMA_BOT = _INT_TOP + 3
_LIGHT_TOP = _CREMA_BOT
_LIGHT_BOT = _LIGHT_TOP + 5
_MED_TOP = _LIGHT_BOT
_MED_BOT = _MED_TOP + 7
_DARK_TOP = _MED_BOT
_DARK_BOT = _DARK_TOP + 7
_DEEP_TOP = _DARK_BOT
_DEEP_BOT = _CUP_BOTTOM - _CUP_WALL

# Handle
_HDL_LEFT = _CUP_RIGHT + 1
_HDL_RIGHT = _CUP_RIGHT + 7
_HDL_TOP = _CUP_TOP + 5
_HDL_BOT = _CUP_BOTTOM - 6

# Saucer
_SAU_LEFT = 13
_SAU_RIGHT = 52
_SAU_TOP = 59
_SAU_BOT = 63

# Table
_TABLE_TOP = 64


def draw_background(img: Image.Image) -> None:
    """Fill the background with a subtle dark scene."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Base: deep navy
    draw.rectangle([0, 0, SCENE_W - 1, SCENE_H - 1], fill=DEEP_NAVY)

    # Upper area: subtle gradient - slightly lighter toward the top center
    # to suggest ambient light from above
    for y in range(0, _CUP_TOP - 2):
        for x in range(_PILLAR_W, SCENE_W - _PILLAR_W):
            # Very subtle - mostly navy with occasional slate highlights
            if (x + y * 3) % 23 == 0:
                px[x, y] = SLATE


def draw_ornate_pillars(img: Image.Image) -> None:
    """Draw decorative PC-98 style pillar borders on left and right."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    for side in (0, 1):  # 0=left, 1=right
        if side == 0:
            x0 = 0
        else:
            x0 = SCENE_W - _PILLAR_W

        # Pillar base color
        draw.rectangle([x0, 0, x0 + _PILLAR_W - 1, SCENE_H - 1], fill=DARK_BROWN)

        # Inner fill with dithered texture
        for y in range(SCENE_H):
            for x in range(x0 + 1, x0 + _PILLAR_W - 1):
                px[x, y] = dither_pick(WARM_BROWN, DARK_BROWN, x, y)

        # Highlight edge (inner side facing the scene)
        inner_x = x0 + _PILLAR_W - 1 if side == 0 else x0
        for y in range(SCENE_H):
            px[inner_x, y] = WARM_GRAY

        # Outer edge
        outer_x = x0 if side == 0 else x0 + _PILLAR_W - 1
        for y in range(SCENE_H):
            px[outer_x, y] = BLACK

        # Decorative diamond/gem patterns every 10 pixels
        mid_x = x0 + _PILLAR_W // 2
        for gem_y in range(5, SCENE_H - 5, 10):
            # Small diamond shape using PC-98 pinks
            px[mid_x, gem_y] = MAGENTA
            px[mid_x, gem_y - 1] = DUSTY_ROSE
            px[mid_x, gem_y + 1] = DUSTY_ROSE
            if mid_x - 1 >= x0 + 1:
                px[mid_x - 1, gem_y] = DUSTY_ROSE
            if mid_x + 1 < x0 + _PILLAR_W - 1:
                px[mid_x + 1, gem_y] = DUSTY_ROSE

        # Horizontal decorative bands every 20 pixels
        for band_y in range(0, SCENE_H, 20):
            for x in range(x0 + 1, x0 + _PILLAR_W - 1):
                px[x, band_y] = MAGENTA
                if band_y + 1 < SCENE_H:
                    px[x, band_y + 1] = DEEP_RED


def draw_window(img: Image.Image) -> None:
    """Draw a window in the background behind the steam area."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Window frame
    wx0 = _PILLAR_W + 8
    wx1 = SCENE_W - _PILLAR_W - 8
    wy0 = 3
    wy1 = 22

    # Window frame (warm gray)
    draw.rectangle([wx0, wy0, wx1, wy1], outline=WARM_GRAY)
    draw.rectangle([wx0 + 1, wy0 + 1, wx1 - 1, wy1 - 1], outline=LIGHT_GRAY)

    # Window pane fill - dark steel blue to suggest sky/outside
    draw.rectangle([wx0 + 2, wy0 + 2, wx1 - 2, wy1 - 2], fill=STEEL_BLUE)

    # Crossbar in the middle
    mid_x = (wx0 + wx1) // 2
    draw.line([(mid_x, wy0 + 2), (mid_x, wy1 - 2)], fill=WARM_GRAY)
    mid_y = (wy0 + wy1) // 2
    draw.line([(wx0 + 2, mid_y), (wx1 - 2, mid_y)], fill=WARM_GRAY)

    # Light from window - subtle warm glow below it
    for y in range(wy1 + 1, wy1 + 4):
        for x in range(wx0 + 3, wx1 - 2):
            if y < SCENE_H and (x + y) % 3 == 0:
                px[x, y] = SLATE

    # Curtain hints on the sides of the window
    for y in range(wy0 + 1, wy1):
        px[wx0 + 2, y] = dither_pick(DEEP_RED, STEEL_BLUE, wx0 + 2, y)
        px[wx1 - 2, y] = dither_pick(DEEP_RED, STEEL_BLUE, wx1 - 2, y)


def draw_table(img: Image.Image) -> None:
    """Draw the table surface with rich wood grain texture."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Base fill
    draw.rectangle([_PILLAR_W, _TABLE_TOP, SCENE_W - _PILLAR_W - 1, SCENE_H - 1],
                    fill=WARM_BROWN)

    # Wood grain bands
    for y in range(_TABLE_TOP, SCENE_H):
        band = (y - _TABLE_TOP) // 3
        base = WARM_GRAY if band % 2 == 0 else WARM_BROWN
        for x in range(_PILLAR_W, SCENE_W - _PILLAR_W):
            px[x, y] = base

    # Lighter grain lines
    for y in range(_TABLE_TOP, SCENE_H, 5):
        for x in range(_PILLAR_W, SCENE_W - _PILLAR_W):
            px[x, y] = LIGHT_GRAY

    # Subtle knots
    for x in range(_PILLAR_W, SCENE_W - _PILLAR_W):
        for y in range(_TABLE_TOP, SCENE_H):
            if (x * 7 + y * 13) % 47 == 0:
                px[x, y] = DARK_BROWN

    # Top edge highlight
    draw.line([(_PILLAR_W, _TABLE_TOP),
               (SCENE_W - _PILLAR_W - 1, _TABLE_TOP)], fill=CREAM)


def draw_cup(img: Image.Image) -> None:
    """Draw the coffee cup with PC-98 style detailed shading."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Outer outline
    draw.rectangle([_CUP_LEFT, _CUP_TOP, _CUP_RIGHT, _CUP_BOTTOM], outline=BLACK)

    # Cup walls with lighting - left bright, right shadowed
    for y in range(_CUP_TOP + 1, _CUP_BOTTOM):
        px[_CUP_LEFT + 1, y] = OFF_WHITE
        px[_CUP_RIGHT - 1, y] = LIGHT_GRAY

    # Rim - 2px with PC-98 rose highlights
    draw.line([(_CUP_LEFT, _CUP_TOP), (_CUP_RIGHT, _CUP_TOP)], fill=BLACK)
    for x in range(_CUP_LEFT + 1, _CUP_RIGHT):
        px[x, _CUP_TOP + 1] = OFF_WHITE
        # Rose highlight accents along the rim
        if x % 4 == 0:
            px[x, _CUP_TOP + 1] = DUSTY_ROSE
        elif x % 4 == 2:
            px[x, _CUP_TOP + 1] = MAGENTA

    # Cup bottom edge
    draw.line([(_CUP_LEFT + 1, _CUP_BOTTOM - 1),
               (_CUP_RIGHT - 1, _CUP_BOTTOM - 1)], fill=LIGHT_GRAY)

    # Coffee fill layers
    _fill_layer(px, _CREMA_TOP, _CREMA_BOT, CREAM, AMBER)
    _fill_layer(px, _LIGHT_TOP, _LIGHT_BOT, CHOCOLATE, AMBER)
    _fill_layer(px, _MED_TOP, _MED_BOT, WARM_BROWN, CHOCOLATE)
    _fill_layer(px, _DARK_TOP, _DARK_BOT, DARK_BROWN, WARM_BROWN)
    _fill_layer(px, _DEEP_TOP, _DEEP_BOT, DARK_BROWN, DARK_BROWN)

    # Layer transitions
    for x in range(_INT_LEFT, _INT_RIGHT + 1):
        if _CREMA_BOT < SCENE_H:
            px[x, _CREMA_BOT] = dither_pick(AMBER, CHOCOLATE, x, _CREMA_BOT)
        if _LIGHT_BOT < SCENE_H:
            px[x, _LIGHT_BOT] = dither_pick(CHOCOLATE, WARM_BROWN, x, _LIGHT_BOT)
        if _MED_BOT < SCENE_H:
            px[x, _MED_BOT] = dither_pick(WARM_BROWN, DARK_BROWN, x, _MED_BOT)

    # Specular highlights on the crema
    for y in range(_CREMA_TOP, min(_CREMA_TOP + 2, _CREMA_BOT)):
        px[_INT_LEFT, y] = OFF_WHITE
        px[_INT_LEFT + 1, y] = OFF_WHITE

    # Reflection/glow on left cup wall from the coffee
    for y in range(_CREMA_TOP, _LIGHT_BOT):
        px[_CUP_LEFT + 1, y] = dither_pick(OFF_WHITE, AMBER, _CUP_LEFT, y)


def _fill_layer(
    px: object,
    y_top: int,
    y_bot: int,
    primary: int,
    accent: int,
) -> None:
    """Fill a coffee layer with primary color and occasional accent dithering."""
    for y in range(y_top, y_bot):
        for x in range(_INT_LEFT, _INT_RIGHT + 1):
            if (x + y) % 5 == 0:
                px[x, y] = dither_pick(primary, accent, x, y)
            else:
                px[x, y] = primary


def draw_handle(img: Image.Image) -> None:
    """Draw the cup handle with shading and highlight."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    draw.rectangle([_HDL_LEFT, _HDL_TOP, _HDL_RIGHT, _HDL_BOT], outline=BLACK)
    draw.rectangle(
        [_HDL_LEFT + 1, _HDL_TOP + 1, _HDL_RIGHT - 1, _HDL_BOT - 1],
        fill=WARM_GRAY,
    )
    # Top highlight
    draw.line([(_HDL_LEFT + 1, _HDL_TOP + 1),
               (_HDL_RIGHT - 1, _HDL_TOP + 1)], fill=OFF_WHITE)
    # Left edge (connects to cup)
    for y in range(_HDL_TOP + 1, _HDL_BOT):
        px[_HDL_LEFT + 1, y] = LIGHT_GRAY

    # Hollow interior
    il = _HDL_LEFT + 3
    ir = _HDL_RIGHT - 1
    it = _HDL_TOP + 3
    ib = _HDL_BOT - 3
    if ir > il and ib > it:
        draw.rectangle([il, it, ir, ib], fill=DEEP_NAVY)
        draw.rectangle([il, it, ir, ib], outline=BLACK)


def draw_saucer(img: Image.Image) -> None:
    """Draw the saucer with highlights and shadow."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], fill=SLATE)
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], outline=BLACK)

    # Top highlight with rose accents
    for x in range(_SAU_LEFT + 1, _SAU_RIGHT):
        px[x, _SAU_TOP + 1] = LIGHT_GRAY
        if x % 5 == 0:
            px[x, _SAU_TOP + 1] = DUSTY_ROSE

    # Shadow below saucer on the table
    shadow_y = max(_SAU_BOT + 1, _TABLE_TOP)
    for y in range(shadow_y, min(shadow_y + 2, SCENE_H)):
        for x in range(_SAU_LEFT + 2, _SAU_RIGHT - 1):
            if _PILLAR_W <= x < SCENE_W - _PILLAR_W:
                px[x, y] = DARK_BROWN
