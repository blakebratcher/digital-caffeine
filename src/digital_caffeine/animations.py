"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

import math
import re

from rich.panel import Panel
from rich.style import Style

from digital_caffeine.constants import Mode

# -- Configuration -----------------------------------------------------------

FPS = 24

# -- Markup-aware layout helpers ---------------------------------------------


def _visible_len(s: str) -> int:
    """Return visible character count, ignoring Rich markup tags."""
    return len(re.sub(r"\[/?[^\]]*\]", "", s))


def _pad_to(s: str, width: int) -> str:
    """Pad string to target visible width, accounting for Rich markup."""
    return s + " " * max(0, width - _visible_len(s))


# -- Procedural steam generation with warm-to-cool gradient ----------------

_STEAM_WIDTH = 25
_STEAM_HEIGHT = 7

# Warm near cup (bottom rows), cooling to gray as steam rises (top rows)
_WISP_COLORS = [
    "#444444",  # row 0 (top) - nearly invisible
    "#555555",  # row 1
    "#666666",  # row 2
    "#888888",  # row 3 - mid gray
    "#997755",  # row 4 - warm tan
    "#AA8866",  # row 5 - warm brown-tan
    "#AA8866",  # row 6 (bottom, near cup) - warmest
]
_TRAIL_COLORS = [
    "#303030",
    "#383838",
    "#444444",
    "#555555",
    "#776655",
    "#886644",
    "#886644",
]

# Heat shimmer characters and colors for bottom 2 rows
_SHIMMER_CHARS = ["*", "\u00b7", "'"]
_SHIMMER_COLORS = ["#FFB347", "#FFA500", "#FF8C00"]


def _generate_steam_frames() -> list[str]:
    """Generate 48 steam frames with warm-to-cool gradient and heat shimmer.

    Wisps start warm near the cup and cool to gray as they rise.
    Occasional shimmer characters appear near the cup in warm orange/gold.
    """
    cx = 12
    num_frames = 48
    age_chars = [")", "~", "'", "\u00b7", ".", "\u00b7", "'"]
    trail_chars = ["~", "'", "\u00b7", ".", " ", " ", " "]
    max_age = 9

    wisps = [
        (0, cx - 2, 1.2, 0.50),
        (1, cx + 1, 1.0, 0.40),
        (2, cx, 0.8, 0.60),
        (3, cx - 1, 1.5, 0.30),
        (4, cx + 2, 1.1, 0.50),
        (5, cx - 3, 0.9, 0.70),
        (6, cx + 1, 1.3, 0.40),
        (0, cx + 3, 0.7, 0.35),
        (3, cx - 3, 1.0, 0.55),
        (5, cx + 2, 1.4, 0.45),
        (1, cx - 4, 1.1, 0.65),
        (7, cx + 3, 0.9, 0.50),
        (2, cx - 1, 1.6, 0.35),
        (4, cx, 0.7, 0.75),
        (6, cx - 2, 1.3, 0.55),
    ]

    frames = []
    for f in range(num_frames):
        char_grid = [[" "] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]
        color_grid = [[None] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]

        for birth, bx, amp, freq in wisps:
            age = (f - birth) % max_age
            row = _STEAM_HEIGHT - 1 - age
            drift = math.sin(f * freq + birth * 0.9) * amp
            x = int(round(bx + drift))

            if 0 <= row < _STEAM_HEIGHT:
                char = age_chars[min(age, len(age_chars) - 1)]
                color = _WISP_COLORS[min(row, len(_WISP_COLORS) - 1)]
                if 0 <= x < _STEAM_WIDTH and char_grid[row][x] == " ":
                    char_grid[row][x] = char
                    color_grid[row][x] = color

            # Trail: one row below, fainter
            tr = row + 1
            if 0 <= tr < _STEAM_HEIGHT and age > 0:
                tc = trail_chars[min(age - 1, len(trail_chars) - 1)]
                tcol = _TRAIL_COLORS[min(tr, len(_TRAIL_COLORS) - 1)]
                tx = int(round(bx + drift * 0.6))
                if (
                    tc != " "
                    and 0 <= tx < _STEAM_WIDTH
                    and char_grid[tr][tx] == " "
                ):
                    char_grid[tr][tx] = tc
                    color_grid[tr][tx] = tcol

        # Heat shimmer in bottom 2 rows
        shimmer_seed = f * 7 + 13
        for row in range(_STEAM_HEIGHT - 2, _STEAM_HEIGHT):
            sx = (shimmer_seed * (row + 1) * 31) % _STEAM_WIDTH
            if char_grid[row][sx] == " " and (shimmer_seed + row) % 5 < 2:
                si = (shimmer_seed + row) % len(_SHIMMER_CHARS)
                char_grid[row][sx] = _SHIMMER_CHARS[si]
                color_grid[row][sx] = _SHIMMER_COLORS[si]

        # Ambient floating particles - faint sparkles drifting in the air
        for p in range(3):
            ap_seed = f * 19 + p * 43
            ar = (ap_seed * 7) % _STEAM_HEIGHT
            ax = (ap_seed * 13 + int(math.sin(f * 0.3 + p) * 2)) % _STEAM_WIDTH
            if char_grid[ar][ax] == " " and (ap_seed % 11) < 3:
                char_grid[ar][ax] = "\u00b7"
                brightness = 0x30 + (ap_seed % 0x20)
                color_grid[ar][ax] = f"#{brightness:02x}{brightness:02x}{brightness:02x}"

        # Render with per-character markup
        frame_lines = []
        for y in range(_STEAM_HEIGHT):
            line = ""
            for x in range(_STEAM_WIDTH):
                c = char_grid[y][x]
                col = color_grid[y][x]
                if c != " " and col:
                    line += f"[{col}]{c}[/]"
                else:
                    line += c
            frame_lines.append(line)
        frames.append("\n".join(frame_lines))
    return frames


STEAM_FRAMES: list[str] = _generate_steam_frames()


def get_steam_frame(frame: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Warm wisps near the cup cool to gray as they rise. Heat shimmer
    sparkles in orange/gold near the cup mouth. Bottom 2 rows pick up
    a tint from the current border hue. Steam advances every 3 display
    frames for natural rising speed at 24 FPS.
    """
    if paused:
        return "\n".join([" " * _STEAM_WIDTH] * _STEAM_HEIGHT)
    sf = (frame // 3) % len(STEAM_FRAMES)
    base = STEAM_FRAMES[sf]

    # Post-process: tint the bottom 2 rows toward the current border hue
    border_hex = BORDER_COLORS[(frame // 2) % len(BORDER_COLORS)]
    lines = base.split("\n")
    for row_idx in range(_STEAM_HEIGHT - 2, _STEAM_HEIGHT):
        if row_idx < len(lines):
            # Replace warm wisp colors with a blend toward border hue
            line = lines[row_idx]
            for old_color in ("#AA8866", "#886644"):
                if old_color in line:
                    # Blend: 50% original warm, 50% border
                    or_ = int(old_color[1:3], 16)
                    og = int(old_color[3:5], 16)
                    ob = int(old_color[5:7], 16)
                    br = int(border_hex[1:3], 16)
                    bg = int(border_hex[3:5], 16)
                    bb = int(border_hex[5:7], 16)
                    nr = int(or_ * 0.5 + br * 0.5)
                    ng = int(og * 0.5 + bg * 0.5)
                    nb = int(ob * 0.5 + bb * 0.5)
                    blended = f"#{nr:02x}{ng:02x}{nb:02x}"
                    line = line.replace(old_color, blended)
            lines[row_idx] = line
    return "\n".join(lines)


# -- Cup art with animated liquid surface, glow, and shimmer ----------------

# 16 ripple patterns (13 chars wide - color applied dynamically)
_SURFACE_CHARS: list[str] = [
    "~\u2248~\u2248~\u2248~\u2248~\u2248~\u2248~",
    "~\u2248\u2248~\u2248~\u2248\u2248~\u2248~\u2248~",
    "\u2248~\u2248~\u2248~\u2248~\u2248~\u2248~\u2248",
    "\u2248~\u2248\u2248~\u2248\u2248~\u2248~\u2248\u2248~",
    "\u2248~~\u2248~~\u2248~~\u2248~\u2248~",
    "~\u2248\u2248~\u2248\u2248~\u2248\u2248~\u2248\u2248~",
    "~\u2248~\u2248\u2248~\u2248~\u2248~\u2248~\u2248",
    "\u2248~\u2248~\u2248\u2248~\u2248~\u2248~\u2248~",
    "~\u2248~\u2248~\u2248~\u2248\u2248~\u2248~\u2248",
    "\u2248\u2248~\u2248~\u2248~\u2248~\u2248~\u2248~",
    "~\u2248\u2248~\u2248~\u2248\u2248~\u2248\u2248~\u2248",
    "\u2248~\u2248\u2248~\u2248~\u2248~\u2248~\u2248~",
    "~\u2248~\u2248\u2248\u2248~\u2248~\u2248~\u2248~",
    "\u2248~\u2248~\u2248~\u2248\u2248\u2248~\u2248~\u2248",
    "\u2248\u2248~\u2248~~\u2248~\u2248\u2248~\u2248~",
    "~\u2248\u2248\u2248~\u2248~\u2248~\u2248~\u2248~",
]


def _surface_color(frame: int) -> str:
    """Return the surface color for the current frame.

    Oscillates between chocolate (#D2691E) and warm gold (#FFB347)
    using sine interpolation over ~4 seconds.
    """
    t = (math.sin(frame / (4 * FPS) * 2 * math.pi) + 1) / 2
    # Interpolate RGB: #D2691E -> #FFB347
    r = int(0xD2 + t * (0xFF - 0xD2))
    g = int(0x69 + t * (0xB3 - 0x69))
    b = int(0x1E + t * (0x47 - 0x1E))
    return f"#{r:02x}{g:02x}{b:02x}"


def _surface_with_shimmer(frame: int) -> str:
    """Build the animated surface line with color glow and shimmer highlights.

    1-2 positions per frame get a gold highlight for light-catching effect.
    """
    pattern_idx = (frame // 3) % len(_SURFACE_CHARS)
    chars = list(_SURFACE_CHARS[pattern_idx])
    color = _surface_color(frame)

    # Deterministic shimmer: replace 1-2 chars with gold highlights
    shimmer_seed = frame * 17 + 7
    for i in range(2):
        pos = (shimmer_seed + i * 11) % len(chars)
        if (shimmer_seed + i) % 7 < 3:
            chars[pos] = "*" if i == 0 else "'"

    # Build markup: shimmer chars get gold, rest get glow color
    result = ""
    for j, ch in enumerate(chars):
        if ch in ("*", "'"):
            result += f"[#FFD700]{ch}[/]"
        else:
            result += f"[{color}]{ch}[/]"
    return result

# Pre-built cup components
_CUP_RIM = "     [#DDDDDD]\u2554" + "\u2550" * 13 + "\u2557[/]    "
_CUP_BOT = "     [#CCCCCC]\u255a" + "\u2550" * 13 + "\u255d[/]    "
_CUP_DIM = "[dim]" + "\u2591" * 13 + "[/]"

# 5-layer coffee gradient: crema -> light -> medium -> dark -> deepest
_FILL_COLORS = [
    ("#D4A574", "#DCBC8A", "#C8955E"),  # crema: tan/cream
    ("#B8520A", "#C45E12", "#A84808"),  # light coffee
    ("#8B4513", "#955020", "#7D3B0E"),  # medium coffee
    ("#5C2E0E", "#6B3610", "#4E260C"),  # dark coffee
    ("#3A1A06", "#452008", "#2E1404"),  # deepest coffee
]
_FILL_CHARS = ["\u2591", "\u2592", "\u2593", "\u2588"]  # ░▒▓█


def _animated_fill_row(frame: int, row_idx: int, width: int = 13) -> str:
    """Generate an animated coffee fill row with per-character bubbling.

    Characters flicker between block densities and color variants,
    creating a subtle simmering PC-98 dithering effect.
    """
    colors = _FILL_COLORS[row_idx]
    # Progressive density: crema=░, light=▒, medium=▓, dark=▓, deepest=█
    base_ci = min(row_idx, len(_FILL_CHARS) - 1)
    base_char = _FILL_CHARS[base_ci]
    result = ""
    seed = frame * 13 + row_idx * 7
    for x in range(width):
        h = (seed + x * 37) % 100
        if h < 15:  # 15% lighter bubble
            char = _FILL_CHARS[max(0, base_ci - 1)]
            color = colors[1]
        elif h < 22:  # 7% darker pocket
            char = _FILL_CHARS[min(len(_FILL_CHARS) - 1, base_ci + 1)]
            color = colors[2]
        else:
            char = base_char
            color = colors[0]
        result += f"[{color}]{char}[/]"
    return result


def _half_block_transition(frame: int, upper_idx: int, lower_idx: int,
                           width: int = 13) -> str:
    """Generate a half-block transition row between two coffee layers.

    Uses ▄ with upper layer as background and lower layer as foreground
    to create smooth PC-98 style dithering between gradient steps.
    """
    result = ""
    seed = frame * 11 + upper_idx * 5
    upper_colors = _FILL_COLORS[upper_idx]
    lower_colors = _FILL_COLORS[lower_idx]
    for x in range(width):
        h = (seed + x * 23) % 100
        # Slight color variation per-character
        if h < 20:
            uc = upper_colors[1]
            lc = lower_colors[1]
        else:
            uc = upper_colors[0]
            lc = lower_colors[0]
        result += f"[{lc} on {uc}]\u2584[/]"
    return result


# Pre-cached paused cup (never changes) - 12 rows to match active
_CUP_PAUSED: str = "\n".join([
    _CUP_RIM,
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2560\u2550\u2550\u2564[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2551[/]  [#CCCCCC]\u2551[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2551[/]  [#CCCCCC]\u2551[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2551[/]  [#CCCCCC]\u2551[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2551[/]  [#CCCCCC]\u2551[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u255f\u2500\u2500\u2568[/]",
    f"     [#CCCCCC]\u2551[/] {_CUP_DIM} [#CCCCCC]\u2551[/]",
    _CUP_BOT,
    "    [#555555]\u2554" + "\u2550" * 17 + "\u2557[/]  ",
    "    [#444444]\u255a" + "\u2550" * 17 + "\u255d[/]  ",
    "      [#2a2a2a]" + "\u2584" * 15 + "[/]    ",
])


def get_cup_art(frame: int, *, paused: bool) -> str:
    """Return the coffee cup ASCII art for the current frame.

    PC-98 style: double-line box drawing, 5-layer coffee gradient with
    half-block dithering transitions, animated crema foam, bubbling fill,
    breathing handle, 3D saucer with shadow.
    """
    if paused:
        return _CUP_PAUSED

    surface = _surface_with_shimmer(frame)

    # Handle breathing: cycle between white and dim white in sync with border
    handle_phase = (frame // 2) % 72
    ht = (math.sin(handle_phase / 72 * 2 * math.pi) + 1) / 2
    hv = int(170 + ht * 85)
    hcolor = f"#{hv:02x}{hv:02x}{hv:02x}"

    # Animated layers
    crema = _animated_fill_row(frame, 0)
    trans_01 = _half_block_transition(frame, 0, 1)
    fill_light = _animated_fill_row(frame, 1)
    fill_med = _animated_fill_row(frame, 2)
    trans_34 = _half_block_transition(frame, 3, 4)
    fill_deep = _animated_fill_row(frame, 4)

    # Saucer reflects border color (30% blend)
    border_hex = BORDER_COLORS[(frame // 2) % len(BORDER_COLORS)]
    br = int(border_hex[1:3], 16)
    bg_ = int(border_hex[3:5], 16)
    bb = int(border_hex[5:7], 16)
    sr = int(0x55 * 0.7 + br * 0.3)
    sg = int(0x55 * 0.7 + bg_ * 0.3)
    sb = int(0x55 * 0.7 + bb * 0.3)
    sc = f"#{sr:02x}{sg:02x}{sb:02x}"
    # Shadow is darker blend
    shr = int(0x2a * 0.8 + br * 0.2)
    shg = int(0x2a * 0.8 + bg_ * 0.2)
    shb = int(0x2a * 0.8 + bb * 0.2)
    shc = f"#{shr:02x}{shg:02x}{shb:02x}"

    lines = [
        _CUP_RIM,
        f"     [#CCCCCC]\u2551[/] {surface}  [{hcolor}]\u2560\u2550\u2550\u2564[/]",
        f"     [#CCCCCC]\u2551[/] {crema} [{hcolor}]\u2551[/]  [{hcolor}]\u2551[/]",
        f"     [#CCCCCC]\u2551[/] {trans_01} [{hcolor}]\u2551[/]  [{hcolor}]\u2551[/]",
        f"     [#CCCCCC]\u2551[/] {fill_light} [{hcolor}]\u2551[/]  [{hcolor}]\u2551[/]",
        f"     [#CCCCCC]\u2551[/] {fill_med} [{hcolor}]\u2551[/]  [{hcolor}]\u2551[/]",
        f"     [#CCCCCC]\u2551[/] {trans_34} [{hcolor}]\u255f\u2500\u2500\u2568[/]",
        f"     [#CCCCCC]\u2551[/] {fill_deep} [{hcolor}]\u2551[/]",
        _CUP_BOT,
        f"    [{sc}]\u2554" + "\u2550" * 17 + "\u2557[/]  ",
        f"    [{sc}]\u255a" + "\u2550" * 17 + "\u255d[/]  ",
        f"      [{shc}]" + "\u2584" * 15 + "[/]    ",
    ]
    return "\n".join(lines)


# -- Coffee drip particles -------------------------------------------------

# Drip spawn columns (within cup walls, columns 6-16 in art space)
_DRIP_COLS = list(range(6, 17))
_DRIP_COLORS = ["#B8520A", "#A0460E", "#8B4513"]


def get_drip_particles(frame: int) -> list[tuple[int, int, str, str]]:
    """Return active drip particles as (row_offset, col, char, color) tuples.

    Drips spawn deterministically based on frame number. Each drip falls
    1-2 rows over 6-10 frames. Max 2 active at once. row_offset is
    relative to just below the cup (0 = first row under saucer).

    Returns a list of (row_offset, col, character, color) tuples.
    """
    drips: list[tuple[int, int, str, str]] = []

    # Check recent spawn windows for active drips
    # Spawn window: one potential drip every ~60 frames (~2.5s at 24 FPS)
    spawn_interval = 60
    lifespan = 8  # frames a drip lives

    for window in range(3):  # check last 3 spawn windows
        spawn_frame = ((frame // spawn_interval) - window) * spawn_interval
        if spawn_frame < 0:
            continue

        # Deterministic spawn decision
        seed = spawn_frame * 31 + 17
        if seed % 5 < 2:  # ~40% chance per window
            age = frame - spawn_frame
            if 0 <= age < lifespan:
                col = _DRIP_COLS[seed % len(_DRIP_COLS)]
                row = age // 3  # fall 1 row every 3 frames
                ci = min(age // 3, len(_DRIP_COLORS) - 1)
                char = "'" if age < lifespan // 2 else "."
                drips.append((row, col, char, _DRIP_COLORS[ci]))

        if len(drips) >= 2:
            break

    return drips[:2]


# -- Smooth HSV rainbow border (72-step hue rotation) ----------------------


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    """Convert HSV (h: 0-360, s: 0-1, v: 0-1) to a hex color string."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    ri = int((r + m) * 255)
    gi = int((g + m) * 255)
    bi = int((b + m) * 255)
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def _generate_border_colors(steps: int = 72) -> list[str]:
    """Generate a full HSV hue rotation at constant saturation and brightness.

    72 steps at S=0.7, V=0.85 for rich but not neon colors.
    Full rotation in ~6 seconds (advance every 2 frames at 24 FPS).
    """
    return [_hsv_to_hex(i * 360 / steps, 0.7, 0.85) for i in range(steps)]


BORDER_COLORS: list[str] = _generate_border_colors()


def get_border_color(frame: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Advances every 2 frames for a full rainbow rotation in ~6 seconds.
    """
    if paused:
        return "yellow"
    return BORDER_COLORS[(frame // 2) % len(BORDER_COLORS)]


# -- Quips with typewriter effect --------------------------------------------

_ALL_QUIPS: list[str] = [
    # -- coffee puns --
    "Brewing productivity...",
    "Espresso yourself freely",
    "A latte work getting done today",
    "Grounds for staying awake",
    "Bean there, done that",
    "Mocha your day productive",
    "Don't lose your tamper",
    "Brew-tally efficient",
    "Affogato what sleep feels like",
    "Pour decisions? Never heard of 'em",
    "Words cannot espresso how awake this PC is",
    "Better latte than never",
    "You mocha me crazy",
    "Sip happens",
    "Thanks a latte",
    "I like big mugs and I cannot lie",
    "Rise and grind",
    "Life begins after coffee",
    "Deja brew: you've had this coffee before",
    "Brew can do it",
    "What's brewin', good lookin'?",
    "Mugs and kisses",
    "The daily grind, literally",
    "Java the Hutt would be proud",
    "No filter needed",
    "Keep calm and drink coffee",
    "Frappe-ning right now: productivity",
    "Cold brew? Never. Hot and alert.",
    "Percolating at maximum efficiency",
    "Another shot? Don't mind if I do",
    "Brewtiful day to stay awake",
    "I've bean thinking about staying awake",
    "Instant coffee is an oxymoron, like instant sleep",
    "Drip, drip, drip... staying awake",
    # -- sleep/awake --
    "Sleep is for the weak (and not this PC)",
    "Your PC refuses to sleep",
    "This machine has a no-nap policy",
    "Insomnia, but make it productive",
    "Your PC is more awake than you are",
    "Counting sheep? This PC doesn't know what sheep are",
    "The only thing sleeping here is your screensaver",
    "This PC runs on pure spite and caffeine",
    "Sleep.exe has been permanently uninstalled",
    "Who needs sleep when you have caffeine?",
    "Power nap? More like power no",
    "This machine hasn't blinked in hours",
    "ZZZ? Not on my watch",
    "Your PC is an insomniac and it's proud",
    "The sandman was denied entry",
    "Wide awake and slightly jittery",
    "No rest for the wicked (or this PC)",
    "Yawning is contagious. Good thing PCs can't yawn.",
    "This PC pulled an all-nighter",
    "Your PC's alarm clock is unnecessary",
    "Lullabies have no power here",
    "Naptime? We don't do that here",
    "Your PC passed the vibe check: awake",
    # -- tech humor --
    "SetThreadExecutionState goes brrr",
    "Keeping the electrons flowing",
    "sudo keep-awake --force --forever",
    "while(true) { stayAwake(); }",
    "Your screensaver is filing a complaint",
    "Power management has left the chat",
    "The screen shall not dim",
    "Task Manager can't stop what it can't see",
    "Your IT admin would not approve",
    "404: Sleep Not Found",
    "Have you tried turning it off and... no. Absolutely not.",
    "This violates at least three energy policies",
    "Connection to sleep server: REFUSED",
    "The power settings have been politely overruled",
    "Kernel panic? More like kernel party",
    "Running hot, staying cool",
    "This process has elevated privileges (to party)",
    "Uptime is the only metric that matters",
    "ping localhost: awake, awake, awake",
    "Thread status: caffeinated",
    "Garbage collection? Not collecting this process",
    "Exception: SleepNotAllowedException",
    "Runtime: forever. Or until Ctrl+C.",
    "Memory leak? No, memory feature",
    # -- workplace --
    "Look busy, stay caffeinated",
    "Your Teams status: permanently green",
    "Productivity level: caffeinated",
    "HR can't prove you weren't at your desk",
    "Working hard or hardly sleeping?",
    "Annual review: never falls asleep on the job",
    "If anyone asks, you've been here the whole time",
    "Meeting in 5. Good thing the screen's still on.",
    "The screensaver is on unpaid leave",
    "This PC is doing the bare minimum... perfectly",
    "Corporate wants you to keep working. PC agrees.",
    "PTO stands for PC Turned On",
    # -- absurd --
    "Somewhere, a bear is jealous of your lack of hibernation",
    "Running on vibes and voltage",
    "The void stares back, but at least the screen is on",
    "Your PC has evolved beyond the need for rest",
    "Powered by caffeine and questionable decisions",
    "The coffee is a metaphor. The wakefulness is literal.",
    "One does not simply let Windows sleep",
    "Instructions unclear, PC now runs on coffee",
    "Your PC's spirit animal is an owl on espresso",
    "In a parallel universe, this PC is napping",
    "This is fine. Everything is fine.",
    "Schr\u00f6dinger's PC: asleep and awake. JK, it's awake.",
    "The mitochondria is the powerhouse. Caffeine is the keep-awake.",
    "Time is an illusion. Uptime doubly so.",
    "Your PC has transcended the sleep-wake cycle",
    # -- self-referential --
    "This animation runs at 24fps. You're welcome.",
    "Handcrafted artisan wakefulness",
    "Small program, big dreams",
    "Still here. Still awake. Still caffeinated.",
    "Keeping it real (and awake)",
    "Just doing my job over here",
    "Your PC is caffeinated",
    "Freshly brewed and wide awake",
    "No decaf allowed here",
    "This machine runs on caffeine",
    "Another cup? Don't mind if I do",
    "Keeping things percolating...",
]


def _shuffle_quips() -> list[str]:
    """Shuffle quip order per-session so each launch feels different."""
    import os
    import random
    rng = random.Random(os.getpid())
    return rng.sample(_ALL_QUIPS, len(_ALL_QUIPS))


QUIPS: list[str] = _shuffle_quips()

PAUSED_QUIP: str = "Gone cold... resume to reheat"

_QUIP_INTERVAL = 12  # seconds per quip


def get_quip(frame: int, *, paused: bool) -> str:
    """Return the current quip with a typewriter reveal effect.

    Characters appear one at a time every 3 frames (~8 chars/sec at 24 FPS)
    with a blinking cursor while typing. Once fully revealed, the cursor
    disappears. Quip order is shuffled per-session.
    """
    if paused:
        return PAUSED_QUIP
    frames_per_quip = _QUIP_INTERVAL * FPS
    quip_idx = (frame // frames_per_quip) % len(QUIPS)
    quip = QUIPS[quip_idx]

    frame_in_quip = frame % frames_per_quip
    # 1 character every 3 frames = ~8 chars/sec at 24 FPS
    chars_to_show = min(len(quip), (frame_in_quip // 3) + 1)

    if chars_to_show < len(quip):
        cursor = "\u2588" if (frame % 18) < 9 else " "
        return quip[:chars_to_show] + cursor
    return quip


# -- Progress bar ------------------------------------------------------------


def _build_progress_bar(
    elapsed: int, total: int, frame: int, width: int = 20
) -> str:
    """Build a rainbow-gradient progress bar for timed sessions.

    Each filled character gets a color from the border palette,
    offset by frame for an animated shimmer effect.
    """
    progress = min(1.0, elapsed / max(1, total))
    filled = int(progress * width)
    pct = int(progress * 100)

    bar = ""
    for i in range(width):
        if i < filled:
            # Rainbow gradient across the bar, shifting with frame
            ci = (i * 3 + frame // 2) % len(BORDER_COLORS)
            bar += f"[{BORDER_COLORS[ci]}]\u2593[/]"
        else:
            bar += "[#333333]\u2591[/]"
    return f"{bar} [dim]{pct}%[/]"


# -- Display assembly --------------------------------------------------------

MODE_DISPLAY: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def format_time(seconds: int) -> str:
    """Format an integer number of seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_animated_display(
    *,
    frame: int,
    mode: Mode,
    uptime_seconds: int,
    duration_seconds: int | None,
    interval: int,
    paused: bool,
    simulate: bool,
) -> Panel:
    """Build an animated Rich Panel showing keep-awake status with coffee art.

    Status fields are vertically centered beside the cup art. Drip particles
    render below the saucer. A progress bar appears when a duration is set.
    """
    steam = get_steam_frame(frame, paused=paused)
    cup = get_cup_art(frame, paused=paused)
    border_color = get_border_color(frame, paused=paused)
    quip = get_quip(frame, paused=paused)

    if paused:
        status_str = "[yellow]Paused[/yellow]"
    else:
        # Pulsing green "Active" text
        gt = (math.sin(frame / FPS * 2 * math.pi) + 1) / 2
        gv = int(0x66 + gt * 0x99)  # pulse between dim and bright green
        status_str = f"[#00{gv:02x}00]Active[/]"

    if duration_seconds is not None:
        remaining = max(0, duration_seconds - uptime_seconds)
        remaining_str = format_time(remaining)
    else:
        remaining_str = "Indefinite"

    sim_str = "[green]On[/green]" if simulate else "[dim]Off[/dim]"

    steam_lines = steam.split("\n")
    cup_lines = cup.split("\n")

    # Drip particle rows (below saucer)
    drip_lines: list[str] = []
    if not paused:
        drips = get_drip_particles(frame)
        if drips:
            # 2 rows of drip space
            drip_grid = [[" "] * _STEAM_WIDTH for _ in range(2)]
            drip_color_grid: list[list[str | None]] = [[None] * _STEAM_WIDTH for _ in range(2)]
            for row_off, col, char, color in drips:
                if 0 <= row_off < 2 and 0 <= col < _STEAM_WIDTH:
                    drip_grid[row_off][col] = char
                    drip_color_grid[row_off][col] = color
            for y in range(2):
                line = ""
                for x in range(_STEAM_WIDTH):
                    c = drip_grid[y][x]
                    col = drip_color_grid[y][x]
                    if c != " " and col:
                        line += f"[{col}]{c}[/]"
                    else:
                        line += c
                drip_lines.append(line)

    art_lines = steam_lines + cup_lines + drip_lines

    # Uptime color pulses with each second
    ut_color = border_color if (frame % FPS) < 2 else "#AAAAAA"
    uptime_str = f"[{ut_color}]{format_time(uptime_seconds)}[/]"

    status_fields = [
        f"Status:         {status_str}",
        f"Mode:           {MODE_DISPLAY.get(mode, str(mode))}",
        f"Uptime:         {uptime_str}",
        f"Time remaining: {remaining_str}",
        f"Interval:       {interval}s",
        f"Simulate:       {sim_str}",
    ]

    if duration_seconds is not None:
        status_fields.append("")
        status_fields.append(
            _build_progress_bar(uptime_seconds, duration_seconds, frame)
        )

    # Vertically center status beside the art
    status_offset = (len(art_lines) - len(status_fields)) // 2
    status_offset = max(0, status_offset)

    art_width = 28
    combined_lines: list[str] = []
    total_rows = max(len(art_lines), len(status_fields) + status_offset)
    for i in range(total_rows):
        left = art_lines[i] if i < len(art_lines) else ""
        si = i - status_offset
        right = ""
        if 0 <= si < len(status_fields):
            right = status_fields[si]
        combined_lines.append(f" {_pad_to(left, art_width)} {right}")

    combined_lines.append("")
    if paused:
        combined_lines.append(
            f" [yellow dim italic]{quip}[/yellow dim italic]"
        )
    else:
        # Quip text gets a warm tint from the surface glow
        quip_color = _surface_color(frame)
        combined_lines.append(f" [{quip_color} italic]{quip}[/]")

    combined_lines.append("")
    # Breathing footer - opacity pulses via gray value
    footer_t = (math.sin(frame / FPS * math.pi) + 1) / 2  # ~2s cycle
    fv = int(60 + footer_t * 50)  # #3C3C3C to #6E6E6E
    footer_color = f"#{fv:02x}{fv:02x}{fv:02x}"
    combined_lines.append(f" [{footer_color}]Press Ctrl+C to stop[/]")

    content = "\n".join(combined_lines)

    # Title matches the border color
    title_str = f"[bold {border_color}]:coffee: Digital Caffeine[/]"

    return Panel(
        content,
        title=title_str,
        border_style=Style(color=border_color),
        padding=(1, 1),
        expand=False,
    )
