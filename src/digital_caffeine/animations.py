"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

import math
import re

from rich.panel import Panel
from rich.style import Style

from digital_caffeine.constants import Mode

# -- Configuration -----------------------------------------------------------

FPS = 4

# -- Markup-aware layout helpers ---------------------------------------------


def _visible_len(s: str) -> int:
    """Return visible character count, ignoring Rich markup tags."""
    return len(re.sub(r"\[/?[^\]]*\]", "", s))


def _pad_to(s: str, width: int) -> str:
    """Pad string to target visible width, accounting for Rich markup."""
    return s + " " * max(0, width - _visible_len(s))


# -- Procedural steam generation ---------------------------------------------

_STEAM_WIDTH = 25
_STEAM_HEIGHT = 5


def _generate_steam_frames() -> list[str]:
    """Generate smooth steam animation frames with multiple rising wisps."""
    cx = 12
    num_frames = 24
    age_chars = [")", "~", "'", "\u00b7", "."]
    max_age = 7

    wisps = [
        (0, cx - 2, 1.2, 0.5),
        (1, cx + 1, 1.0, 0.4),
        (2, cx, 0.8, 0.6),
        (3, cx - 1, 1.5, 0.3),
        (4, cx + 2, 1.1, 0.5),
        (5, cx - 2, 0.9, 0.7),
        (6, cx + 1, 1.3, 0.4),
    ]

    frames = []
    for f in range(num_frames):
        grid = [[" "] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]
        for birth, bx, amp, freq in wisps:
            age = (f - birth) % max_age
            row = _STEAM_HEIGHT - 1 - age
            if 0 <= row < _STEAM_HEIGHT:
                drift = math.sin(f * freq + birth * 0.9) * amp
                x = int(round(bx + drift))
                char = age_chars[min(age, len(age_chars) - 1)]
                if 0 <= x < _STEAM_WIDTH and grid[row][x] == " ":
                    grid[row][x] = char
        frames.append("\n".join("".join(row) for row in grid))
    return frames


STEAM_FRAMES: list[str] = _generate_steam_frames()


def get_steam_frame(frame: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Args:
        frame: Animation frame counter.
        paused: Whether the engine is paused.

    Returns:
        A multi-line string of steam art with dim markup, or blank lines if paused.
    """
    if paused:
        return "\n".join([" " * _STEAM_WIDTH] * _STEAM_HEIGHT)
    raw = STEAM_FRAMES[frame % len(STEAM_FRAMES)]
    return "\n".join(f"[dim]{line}[/]" for line in raw.split("\n"))


# -- Cup art with animated liquid surface ------------------------------------

_SURFACE_PATTERNS: list[str] = [
    "[#D2691E]\u007e\u2248\u007e\u2248\u007e\u2248\u007e\u2248\u007e\u2248\u007e[/]",
    "[#D2691E]\u2248\u007e\u2248\u007e\u2248\u007e\u2248\u007e\u2248\u007e\u2248[/]",
    "[#D2691E]\u007e\u2248\u2248\u007e\u2248\u2248\u007e\u2248\u2248\u007e\u2248[/]",
    "[#D2691E]\u2248\u007e\u007e\u2248\u007e\u007e\u2248\u007e\u007e\u2248\u007e[/]",
]


def get_cup_art(frame: int, *, paused: bool) -> str:
    """Return the coffee cup ASCII art for the current frame.

    Active cups have colored coffee fill with an animated liquid surface.
    Paused cups show dimmed fill.

    Args:
        frame: Animation frame counter (used for surface ripple).
        paused: Whether the engine is paused.

    Returns:
        A multi-line string of cup art with Rich markup.
    """
    _top = "     \u250c" + "\u2500" * 13 + "\u2510    "
    _bot = "     \u2514" + "\u2500" * 13 + "\u2518    "
    _saucer = "    [dim]" + "\u2550" * 19 + "[/]  "
    _dim_fill = "[dim]" + "\u2591" * 11 + "[/]"
    _hot_fill = "[#8B6914]" + "\u2593" * 11 + "[/]"

    if paused:
        lines = [
            _top,
            f"     \u2502 {_dim_fill} \u251c\u2500\u2500\u256e",
            f"     \u2502 {_dim_fill} \u2502  \u2502",
            f"     \u2502 {_dim_fill} \u2502  \u2502",
            f"     \u2502 {_dim_fill} \u251c\u2500\u2500\u256f",
            _bot,
            _saucer,
        ]
    else:
        surface = _SURFACE_PATTERNS[
            (frame // 2) % len(_SURFACE_PATTERNS)
        ]
        lines = [
            _top,
            f"     \u2502 {surface} \u251c\u2500\u2500\u256e",
            f"     \u2502 {_hot_fill} \u2502  \u2502",
            f"     \u2502 {_hot_fill} \u2502  \u2502",
            f"     \u2502 {_hot_fill} \u251c\u2500\u2500\u256f",
            _bot,
            _saucer,
        ]
    return "\n".join(lines)


# -- Border colors (8-step breathing cycle) ----------------------------------

BORDER_COLORS: list[str] = [
    "bright_cyan",
    "cyan",
    "dark_cyan",
    "dark_cyan",
    "dark_cyan",
    "cyan",
    "bright_cyan",
    "cyan",
]


def get_border_color(frame: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Changes every FPS//2 frames (twice per second) for a smooth breathing effect.

    Args:
        frame: Animation frame counter.
        paused: Whether the engine is paused.

    Returns:
        A Rich color name string.
    """
    if paused:
        return "yellow"
    step = max(1, FPS // 2)
    return BORDER_COLORS[(frame // step) % len(BORDER_COLORS)]


# -- Quips -------------------------------------------------------------------

QUIPS: list[str] = [
    "Brewing productivity...",
    "Your PC is caffeinated",
    "Sleep is for the weak (and not this PC)",
    "Keeping things percolating...",
    "Another cup? Don't mind if I do",
    "Drip, drip, drip... staying awake",
    "Freshly brewed and wide awake",
    "No decaf allowed here",
    "Espresso yourself freely",
    "A latte work getting done today",
    "Grounds for staying awake",
    "This machine runs on caffeine",
]

PAUSED_QUIP: str = "Gone cold... resume to reheat"


def get_quip(frame: int, *, paused: bool) -> str:
    """Return the current quip message.

    Rotates every 8 seconds (8 * FPS frames).

    Args:
        frame: Animation frame counter.
        paused: Whether the engine is paused.

    Returns:
        A quip string.
    """
    if paused:
        return PAUSED_QUIP
    frames_per_quip = 8 * FPS
    return QUIPS[(frame // frames_per_quip) % len(QUIPS)]


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

    Args:
        frame: Animation frame counter (increments at FPS rate).
        mode: Active prevention mode.
        uptime_seconds: How long the engine has been running.
        duration_seconds: Total requested duration (None if indefinite).
        interval: Refresh interval in seconds.
        paused: Whether the engine is currently paused.
        simulate: Whether input simulation is enabled.

    Returns:
        A Rich Panel with animated coffee cup, status info, and a quip.
    """
    steam = get_steam_frame(frame, paused=paused)
    cup = get_cup_art(frame, paused=paused)
    border_color = get_border_color(frame, paused=paused)
    quip = get_quip(frame, paused=paused)

    status_str = "[yellow]Paused[/yellow]" if paused else "[green]Active[/green]"

    if duration_seconds is not None:
        remaining = max(0, duration_seconds - uptime_seconds)
        remaining_str = format_time(remaining)
    else:
        remaining_str = "Indefinite"

    sim_str = "[green]On[/green]" if simulate else "[dim]Off[/dim]"

    steam_lines = steam.split("\n")
    cup_lines = cup.split("\n")
    art_lines = steam_lines + cup_lines

    status_fields = [
        f"Status:         {status_str}",
        f"Mode:           {MODE_DISPLAY.get(mode, str(mode))}",
        f"Uptime:         {format_time(uptime_seconds)}",
        f"Time remaining: {remaining_str}",
        f"Interval:       {interval}s",
        f"Simulate:       {sim_str}",
    ]

    art_width = 27
    combined_lines: list[str] = []
    max_rows = max(len(art_lines), len(status_fields))
    for i in range(max_rows):
        left = art_lines[i] if i < len(art_lines) else ""
        right = status_fields[i] if i < len(status_fields) else ""
        combined_lines.append(f"  {_pad_to(left, art_width)} {right}")

    combined_lines.append("")
    if paused:
        combined_lines.append(f"  [yellow dim italic]{quip}[/yellow dim italic]")
    else:
        combined_lines.append(f"  [dim italic]{quip}[/dim italic]")

    combined_lines.append("")
    combined_lines.append("  [dim]Press Ctrl+C to stop[/dim]")

    content = "\n".join(combined_lines)
    return Panel(
        content,
        title="[bold cyan]:coffee: Digital Caffeine[/bold cyan]",
        border_style=Style(color=border_color),
        padding=(1, 2),
    )
