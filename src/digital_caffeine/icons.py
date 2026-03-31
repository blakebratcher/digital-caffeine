"""Programmatic icon generation for Digital Caffeine system tray.

Uses Pillow to draw simple coffee cup icons at runtime, avoiding the need
for external icon files.
"""

from __future__ import annotations

from PIL import Image, ImageDraw


def _draw_cup_body(draw: ImageDraw.ImageDraw, size: int, color: str, fill: bool) -> None:
    """Draw the main coffee cup body (a slightly tapered rectangle).

    The cup occupies roughly the center-lower portion of the icon canvas.
    """
    # Cup body bounds - leave room for steam above and handle to the right
    left = int(size * 0.18)
    right = int(size * 0.65)
    top = int(size * 0.38)
    bottom = int(size * 0.85)

    # Slight taper: top is a bit wider than bottom
    taper = int(size * 0.04)

    body = [
        (left - taper, top),       # top-left (wider)
        (right + taper, top),      # top-right (wider)
        (right, bottom),           # bottom-right
        (left, bottom),            # bottom-left
    ]

    if fill:
        draw.polygon(body, fill=color, outline=color)
    else:
        draw.polygon(body, fill=None, outline=color)
        # Draw with a slightly thicker look by drawing again offset by 1px
        draw.line(body + [body[0]], fill=color, width=max(2, size // 24))


def _draw_handle(draw: ImageDraw.ImageDraw, size: int, color: str, fill: bool) -> None:
    """Draw the cup handle as an arc on the right side."""
    # The handle sits on the right side of the cup, vertically centered
    handle_left = int(size * 0.63)
    handle_top = int(size * 0.45)
    handle_right = int(size * 0.85)
    handle_bottom = int(size * 0.72)

    width = max(2, size // 16)
    if fill:
        width = max(3, size // 12)

    draw.arc(
        [handle_left, handle_top, handle_right, handle_bottom],
        start=-90,
        end=90,
        fill=color,
        width=width,
    )


def _draw_steam(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    """Draw small wavy steam lines above the cup."""
    # Three small steam curves above the cup
    cup_top = int(size * 0.38)
    steam_positions = [
        int(size * 0.30),
        int(size * 0.42),
        int(size * 0.54),
    ]

    for x in steam_positions:
        # Each steam line is a small S-curve drawn as two arcs
        steam_bottom = cup_top - int(size * 0.03)
        steam_mid = cup_top - int(size * 0.14)
        steam_top = cup_top - int(size * 0.25)
        wave = int(size * 0.05)
        width = max(1, size // 32)

        # Lower curve (bends right)
        draw.arc(
            [x - wave, steam_mid, x + wave, steam_bottom],
            start=0,
            end=180,
            fill=color,
            width=width,
        )
        # Upper curve (bends left)
        draw.arc(
            [x - wave, steam_top, x + wave, steam_mid],
            start=180,
            end=360,
            fill=color,
            width=width,
        )


def _draw_saucer(draw: ImageDraw.ImageDraw, size: int, color: str) -> None:
    """Draw a small saucer line beneath the cup."""
    left = int(size * 0.12)
    right = int(size * 0.72)
    y = int(size * 0.88)
    width = max(2, size // 20)
    draw.line([(left, y), (right, y)], fill=color, width=width)


def create_active_icon(size: int = 64) -> Image.Image:
    """Create a filled coffee cup icon representing the active state.

    Uses a warm brown color with steam lines to convey "hot coffee" / active.

    Args:
        size: Icon dimensions in pixels (square).

    Returns:
        RGBA PIL Image with the active icon.
    """
    color = "#6F4E37"
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    _draw_steam(draw, size, color)
    _draw_cup_body(draw, size, color, fill=True)
    _draw_handle(draw, size, color, fill=True)
    _draw_saucer(draw, size, color)

    return img


def create_paused_icon(size: int = 64) -> Image.Image:
    """Create an outlined coffee cup icon representing the paused state.

    Uses a medium gray color with no steam lines to convey "paused".

    Args:
        size: Icon dimensions in pixels (square).

    Returns:
        RGBA PIL Image with the paused icon.
    """
    color = "#888888"
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # No steam - paused
    _draw_cup_body(draw, size, color, fill=False)
    _draw_handle(draw, size, color, fill=False)
    _draw_saucer(draw, size, color)

    return img


def create_stopped_icon(size: int = 64) -> Image.Image:
    """Create a light outlined empty cup icon representing the stopped state.

    Uses a light gray color with no steam to convey "session ended".

    Args:
        size: Icon dimensions in pixels (square).

    Returns:
        RGBA PIL Image with the stopped icon.
    """
    color = "#BBBBBB"
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # No steam - stopped
    _draw_cup_body(draw, size, color, fill=False)
    _draw_handle(draw, size, color, fill=False)
    _draw_saucer(draw, size, color)

    return img
