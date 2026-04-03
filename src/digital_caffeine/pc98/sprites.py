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
    DUSTY_ROSE,
    LIGHT_GRAY,
    OFF_WHITE,
    SLATE,
    WARM_BROWN,
    WARM_GRAY,
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
    """Fill the scene with a calm deep navy. Subtle, not flashy."""
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, SCENE_W - 1, SCENE_H - 1], fill=DEEP_NAVY)
    # Sparse twinkling stars - just a few faint pixels in the upper region
    px = img.load()
    star_positions = [
        (5, 3), (15, 8), (52, 5), (60, 12), (8, 18), (38, 2),
        (45, 15), (22, 10), (58, 22), (3, 14), (30, 6), (50, 20),
    ]
    for sx, sy in star_positions:
        if 0 <= sx < SCENE_W and 0 <= sy < _CUP_TOP - 3:
            px[sx, sy] = SLATE  # dim star, not bright


def draw_table(img: Image.Image) -> None:
    """Draw the table surface with rich wood grain texture."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Base table fill
    draw.rectangle([0, _TABLE_TOP, SCENE_W - 1, SCENE_H - 1], fill=WARM_BROWN)

    # Wood grain: alternating lighter/darker horizontal bands
    for y in range(_TABLE_TOP, SCENE_H):
        band = (y - _TABLE_TOP) // 3
        if band % 2 == 0:
            for x in range(SCENE_W):
                px[x, y] = WARM_GRAY
        # Lighter grain highlight every 6 rows
        if (y - _TABLE_TOP) % 6 == 0:
            draw.line([(0, y), (SCENE_W - 1, y)], fill=LIGHT_GRAY)

    # Subtle knot patterns - small darker circles in the wood
    for x in range(SCENE_W):
        for y in range(_TABLE_TOP, SCENE_H):
            if (x * 7 + y * 13) % 47 == 0:
                px[x, y] = DARK_BROWN

    # Table edge highlight at the very top
    draw.line([(0, _TABLE_TOP), (SCENE_W - 1, _TABLE_TOP)], fill=LIGHT_GRAY)


def draw_cup(img: Image.Image) -> None:
    """Draw the coffee cup body with gradient fill layers and PC-98 highlights."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Outer outline (black)
    draw.rectangle(
        [_CUP_LEFT, _CUP_TOP, _CUP_RIGHT, _CUP_BOTTOM], outline=BLACK
    )

    # Cup walls - left wall lighter (light source from left), right wall darker
    for y in range(_CUP_TOP + 1, _CUP_BOTTOM):
        px[_CUP_LEFT + 1, y] = OFF_WHITE  # left wall highlight
        px[_CUP_RIGHT - 1, y] = LIGHT_GRAY  # right wall shadow

    # Rim - the star of the cup. 3px thick with PC-98 magenta/rose glow
    draw.rectangle(
        [_CUP_LEFT + 1, _CUP_TOP, _CUP_RIGHT - 1, _CUP_TOP], fill=BLACK
    )
    draw.rectangle(
        [_CUP_LEFT + 1, _CUP_TOP + 1, _CUP_RIGHT - 1, _CUP_TOP + 1], fill=OFF_WHITE
    )
    # PC-98 signature: magenta/rose highlight along the rim
    for x in range(_CUP_LEFT + 2, _CUP_RIGHT - 1):
        if x % 3 == 0:
            px[x, _CUP_TOP + 1] = DUSTY_ROSE

    # Cup bottom inner edge
    draw.line(
        [(_CUP_LEFT + 1, _CUP_BOTTOM - 1), (_CUP_RIGHT - 1, _CUP_BOTTOM - 1)],
        fill=LIGHT_GRAY,
    )

    # Coffee fill layers with ordered dithering at boundaries
    _fill_layer(px, _CREMA_TOP, _CREMA_BOT, CREAM, AMBER)
    _fill_layer(px, _LIGHT_TOP, _LIGHT_BOT, CHOCOLATE, AMBER)
    _fill_layer(px, _MED_TOP, _MED_BOT, WARM_BROWN, CHOCOLATE)
    _fill_layer(px, _DARK_TOP, _DARK_BOT, DARK_BROWN, WARM_BROWN)
    _fill_layer(px, _DEEP_TOP, _DEEP_BOT, DARK_BROWN, DARK_BROWN)

    # Dithered transitions between layers
    for x in range(_INT_LEFT, _INT_RIGHT + 1):
        if _CREMA_BOT < SCENE_H:
            px[x, _CREMA_BOT] = dither_pick(AMBER, CHOCOLATE, x, _CREMA_BOT)
        if _LIGHT_BOT < SCENE_H:
            px[x, _LIGHT_BOT] = dither_pick(CHOCOLATE, WARM_BROWN, x, _LIGHT_BOT)
        if _MED_BOT < SCENE_H:
            px[x, _MED_BOT] = dither_pick(WARM_BROWN, DARK_BROWN, x, _MED_BOT)
        if _DARK_BOT < SCENE_H:
            px[x, _DARK_BOT] = dither_pick(DARK_BROWN, DARK_BROWN, x, _DARK_BOT)

    # Specular highlight on the left wall of the coffee (light catching the rim)
    for y in range(_CREMA_TOP, min(_CREMA_TOP + 2, _CREMA_BOT)):
        px[_INT_LEFT, y] = OFF_WHITE
        px[_INT_LEFT + 1, y] = AMBER


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
    """Draw the cup handle with PC-98 style shading."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Outline
    draw.rectangle([_HDL_LEFT, _HDL_TOP, _HDL_RIGHT, _HDL_BOT], outline=BLACK)
    # Fill
    draw.rectangle(
        [_HDL_LEFT + 1, _HDL_TOP + 1, _HDL_RIGHT - 1, _HDL_BOT - 1],
        fill=WARM_GRAY,
    )
    # Top edge highlight
    draw.line(
        [(_HDL_LEFT + 1, _HDL_TOP + 1), (_HDL_RIGHT - 1, _HDL_TOP + 1)],
        fill=OFF_WHITE,
    )
    # Left edge highlight (connects to cup)
    for y in range(_HDL_TOP + 1, _HDL_BOT):
        px[_HDL_LEFT + 1, y] = LIGHT_GRAY

    # Hollow interior
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
    """Draw the saucer with highlight, shadow, and reflection."""
    draw = ImageDraw.Draw(img)
    px = img.load()

    # Main saucer body
    draw.rectangle([_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], fill=SLATE)
    draw.rectangle(
        [_SAU_LEFT, _SAU_TOP, _SAU_RIGHT, _SAU_BOT], outline=BLACK
    )
    # Top highlight - bright edge catches the light
    draw.line(
        [(_SAU_LEFT + 1, _SAU_TOP + 1), (_SAU_RIGHT - 1, _SAU_TOP + 1)],
        fill=LIGHT_GRAY,
    )
    # PC-98 magenta glint on the saucer edge
    for x in range(_SAU_LEFT + 3, _SAU_RIGHT - 2, 5):
        px[x, _SAU_TOP + 1] = DUSTY_ROSE

    # Shadow below saucer - darker than table, blends into wood
    shadow_y = _SAU_BOT + 1
    if shadow_y < _TABLE_TOP:
        shadow_y = _TABLE_TOP
    for y in range(shadow_y, min(shadow_y + 2, SCENE_H)):
        for x in range(_SAU_LEFT + 2, _SAU_RIGHT - 1):
            if 0 <= x < SCENE_W and 0 <= y < SCENE_H:
                px[x, y] = DARK_BROWN
