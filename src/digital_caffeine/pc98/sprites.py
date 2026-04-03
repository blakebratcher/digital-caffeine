"""PC-98 pixel art sprite drawing functions.

All functions draw onto a Pillow palette-mode Image using palette indices.
Coordinate system: (0,0) is top-left. Scene is SCENE_W x SCENE_H pixels.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from digital_caffeine.pc98.palette import (
    BLACK, DEEP_NAVY, DARK_BROWN, WARM_BROWN, CHOCOLATE, AMBER,
    GOLD, CREAM, SLATE, WARM_GRAY, LIGHT_GRAY, OFF_WHITE,
    dither_pick,
)

# Scene dimensions (pixels)
SCENE_W = 64
SCENE_H = 80

# -- Layout constants ---------------------------------------------------------

# Cup body (outer edges, including 1px outline)
_CUP_LEFT = 17
_CUP_RIGHT = 46
_CUP_TOP = 27
_CUP_BOTTOM = 58
_CUP_WALL = 2       # wall thickness including outline

# Cup interior (inside walls)
_INT_LEFT = _CUP_LEFT + _CUP_WALL
_INT_RIGHT = _CUP_RIGHT - _CUP_WALL
_INT_TOP = _CUP_TOP + 2  # below rim

# Coffee fill layer boundaries (y coordinates, interior)
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
_HDL_RIGHT = _CUP_RIGHT + 8
_HDL_TOP = _CUP_TOP + 5
_HDL_BOT = _CUP_BOTTOM - 6

# Saucer
_SAU_LEFT = 12
_SAU_RIGHT = 51
_SAU_TOP = 59
_SAU_BOT = 63

# Table
_TABLE_TOP = 64


def draw_background(img: Image.Image) -> None:
    """Fill the scene with deep navy + black 2x2 dither pattern."""
    px = img.load()
    for y in range(SCENE_H):
        for x in range(SCENE_W):
            px[x, y] = dither_pick(DEEP_NAVY, BLACK, x, y)


def draw_table(img: Image.Image) -> None:
    """Draw the table surface in the lower portion of the scene."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, _TABLE_TOP, SCENE_W - 1, SCENE_H - 1], fill=WARM_GRAY)
    # Wood grain: lighter horizontal lines every 4 pixels
    for y in range(_TABLE_TOP, SCENE_H, 4):
        draw.line([(0, y), (SCENE_W - 1, y)], fill=LIGHT_GRAY)
    # Subtle dithered texture
    px = img.load()
    for y in range(_TABLE_TOP + 1, SCENE_H):
        for x in range(SCENE_W):
            if (x + y) % 7 == 0:
                px[x, y] = dither_pick(WARM_GRAY, WARM_BROWN, x, y)


def draw_cup(img: Image.Image) -> None:
    """Draw the coffee cup body with gradient fill layers."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Outer outline (black)
    draw.rectangle(
        [_CUP_LEFT, _CUP_TOP, _CUP_RIGHT, _CUP_BOTTOM], outline=BLACK
    )
    # Cup walls (light gray)
    draw.rectangle(
        [_CUP_LEFT + 1, _CUP_TOP + 1, _CUP_RIGHT - 1, _CUP_BOTTOM - 1],
        outline=LIGHT_GRAY,
    )
    # Rim highlight (off-white top 2 rows)
    draw.rectangle(
        [_CUP_LEFT + 1, _CUP_TOP, _CUP_RIGHT - 1, _CUP_TOP + 1], fill=OFF_WHITE
    )
    draw.rectangle(
        [_CUP_LEFT, _CUP_TOP, _CUP_RIGHT, _CUP_TOP], fill=BLACK
    )

    # Coffee fill layers with ordered dithering at boundaries
    _fill_layer(px, _CREMA_TOP, _CREMA_BOT, CREAM, AMBER)
    _fill_layer(px, _LIGHT_TOP, _LIGHT_BOT, CHOCOLATE, AMBER)
    _fill_layer(px, _MED_TOP, _MED_BOT, WARM_BROWN, CHOCOLATE)
    _fill_layer(px, _DARK_TOP, _DARK_BOT, DARK_BROWN, WARM_BROWN)
    _fill_layer(px, _DEEP_TOP, _DEEP_BOT, DARK_BROWN, DARK_BROWN)

    # Dithered boundaries between layers (1px transition rows)
    for x in range(_INT_LEFT, _INT_RIGHT + 1):
        if _CREMA_BOT < SCENE_H:
            px[x, _CREMA_BOT] = dither_pick(AMBER, CHOCOLATE, x, _CREMA_BOT)
        if _LIGHT_BOT < SCENE_H:
            px[x, _LIGHT_BOT] = dither_pick(CHOCOLATE, WARM_BROWN, x, _LIGHT_BOT)
        if _MED_BOT < SCENE_H:
            px[x, _MED_BOT] = dither_pick(WARM_BROWN, DARK_BROWN, x, _MED_BOT)
        if _DARK_BOT < SCENE_H:
            px[x, _DARK_BOT] = dither_pick(DARK_BROWN, DARK_BROWN, x, _DARK_BOT)


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
    """Draw the cup handle to the right of the cup body."""
    draw = ImageDraw.Draw(img)
    # Outline
    draw.rectangle([_HDL_LEFT, _HDL_TOP, _HDL_RIGHT, _HDL_BOT], outline=BLACK)
    # Fill
    draw.rectangle(
        [_HDL_LEFT + 1, _HDL_TOP + 1, _HDL_RIGHT - 1, _HDL_BOT - 1],
        fill=WARM_GRAY,
    )
    # Highlight on top edge
    draw.line(
        [(_HDL_LEFT + 1, _HDL_TOP + 1), (_HDL_RIGHT - 1, _HDL_TOP + 1)],
        fill=OFF_WHITE,
    )
    # Hollow interior (cut out the middle to make it a handle shape)
    inner_left = _HDL_LEFT + 3
    inner_right = _HDL_RIGHT - 2
    inner_top = _HDL_TOP + 3
    inner_bot = _HDL_BOT - 3
    if inner_right > inner_left and inner_bot > inner_top:
        draw.rectangle(
            [inner_left, inner_top, inner_right, inner_bot], fill=DEEP_NAVY
        )
        draw.rectangle(
            [inner_left, inner_top, inner_right, inner_bot], outline=BLACK
        )


def draw_saucer(img: Image.Image) -> None:
    """Draw the saucer below the cup."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], fill=SLATE)
    draw.rectangle(
        [_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], outline=BLACK
    )
    draw.line(
        [(_SAU_LEFT + 1, _SAU_TOP + 1), (_SAU_RIGHT - 1, _SAU_TOP + 1)],
        fill=LIGHT_GRAY,
    )
