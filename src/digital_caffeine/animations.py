"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

from rich.panel import Panel
from rich.style import Style

from digital_caffeine.constants import Mode

# -- Steam frames (4 frames, each 2 lines tall) ------------------------------
# Characters cycle upward to create a rising-steam illusion.

STEAM_FRAMES: list[str] = [
    "    ~ ~  \n   ( _ ) ",
    "   ( _ ) \n    ~ ~  ",
    "   ~ . ~ \n  (  ~  )",
    "  (  ~  )\n   ~ . ~ ",
]

_BLANK_STEAM: str = "         \n         "


def get_steam_frame(elapsed: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A two-line string of steam art, or blank lines if paused.
    """
    if paused:
        return _BLANK_STEAM
    return STEAM_FRAMES[elapsed % len(STEAM_FRAMES)]


# -- Cup art ------------------------------------------------------------------

_CUP_ACTIVE: str = (
    "   ┌───────┐ ┐\n"
    "   │▓▓▓▓▓▓▓│ │\n"
    "   └───────┘ ┘"
)

_CUP_PAUSED: str = (
    "   ┌───────┐ ┐\n"
    "   │░░░░░░░│ │\n"
    "   └───────┘ ┘"
)


def get_cup_art(*, paused: bool) -> str:
    """Return the coffee cup ASCII art.

    Args:
        paused: Whether the engine is paused (shows dim fill).

    Returns:
        A three-line string of cup art.
    """
    return _CUP_PAUSED if paused else _CUP_ACTIVE


# -- Border colors (4-step color cycle) -----------------------------------

BORDER_COLORS: list[str] = ["cyan", "dark_cyan", "bright_cyan", "dark_cyan"]


def get_border_color(elapsed: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A Rich color name string.
    """
    if paused:
        return "yellow"
    return BORDER_COLORS[elapsed % len(BORDER_COLORS)]


# -- Quips --------------------------------------------------------------------

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


def get_quip(elapsed: int, *, paused: bool) -> str:
    """Return the current quip message.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A quip string.
    """
    if paused:
        return PAUSED_QUIP
    return QUIPS[(elapsed // 8) % len(QUIPS)]


# Maps Mode enum to display labels
_MODE_DISPLAY: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def _format_time(seconds: int) -> str:
    """Format an integer number of seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_animated_display(
    *,
    mode: Mode,
    uptime_seconds: int,
    duration_seconds: int | None,
    interval: int,
    paused: bool,
    simulate: bool,
) -> Panel:
    """Build an animated Rich Panel showing keep-awake status with coffee art.

    Args:
        mode: Active prevention mode.
        uptime_seconds: How long the engine has been running.
        duration_seconds: Total requested duration (None if indefinite).
        interval: Refresh interval in seconds.
        paused: Whether the engine is currently paused.
        simulate: Whether input simulation is enabled.

    Returns:
        A Rich Panel with animated coffee cup, status info, and a quip.
    """
    steam = get_steam_frame(uptime_seconds, paused=paused)
    cup = get_cup_art(paused=paused)
    border_color = get_border_color(uptime_seconds, paused=paused)
    quip = get_quip(uptime_seconds, paused=paused)

    # Status values
    status_str = "[yellow]Paused[/yellow]" if paused else "[green]Active[/green]"

    if duration_seconds is not None:
        remaining = max(0, duration_seconds - uptime_seconds)
        remaining_str = _format_time(remaining)
    else:
        remaining_str = "Indefinite"

    sim_str = "[green]On[/green]" if simulate else "[dim]Off[/dim]"

    # Build the two-column layout as aligned text lines.
    # Left column: steam (2 lines) + cup (3 lines) = 5 art lines
    # Right column: status fields aligned beside the art
    steam_lines = steam.split("\n")
    cup_lines = cup.split("\n")
    art_lines = steam_lines + cup_lines

    status_fields = [
        f"Status:         {status_str}",
        f"Mode:           {_MODE_DISPLAY.get(mode, str(mode))}",
        f"Uptime:         {_format_time(uptime_seconds)}",
        f"Time remaining: {remaining_str}",
        f"Interval:       {interval}s",
    ]

    # Pad art lines to a uniform width for alignment
    art_width = 20
    combined_lines: list[str] = []
    max_rows = max(len(art_lines), len(status_fields))
    for i in range(max_rows):
        left = art_lines[i] if i < len(art_lines) else ""
        right = status_fields[i] if i < len(status_fields) else ""
        combined_lines.append(f"  {left:<{art_width}} {right}")

    # Simulate line (below the main grid)
    combined_lines.append(f"  {'':>{art_width}} Simulate:       {sim_str}")

    # Quip line
    combined_lines.append("")
    if paused:
        combined_lines.append(f"  [yellow dim italic]{quip}[/yellow dim italic]")
    else:
        combined_lines.append(f"  [dim italic]{quip}[/dim italic]")

    # Ctrl+C hint
    combined_lines.append("")
    combined_lines.append("  [dim]Press Ctrl+C to stop[/dim]")

    content = "\n".join(combined_lines)
    return Panel(
        content,
        title="[bold cyan]:coffee: Digital Caffeine[/bold cyan]",
        border_style=Style(color=border_color),
        padding=(1, 2),
    )
