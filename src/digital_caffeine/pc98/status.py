"""PC-98 styled status panel for the right side of the display."""

from __future__ import annotations

from digital_caffeine.pc98.palette import (
    DUSTY_ROSE,
    GOLD,
    MAGENTA,
    OFF_WHITE,
    PALETTE,
    STEEL_BLUE,
)

_H = "\u2500"   # horizontal line
_V = "\u2502"   # vertical line
_TL = "\u250c"  # top-left corner
_TR = "\u2510"  # top-right corner
_BL = "\u2514"  # bottom-left corner
_BR = "\u2518"  # bottom-right corner
_DIAMOND = "\u25c6"


def _format_time(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_status_text(
    *,
    active: bool,
    paused: bool,
    mode_label: str,
    uptime_seconds: int,
    remaining_str: str,
    interval: int,
    simulate: bool,
    frame: int,
    progress_pct: int | None = None,
) -> str:
    gold = PALETTE[GOLD]
    blue = PALETTE[STEEL_BLUE]
    white = PALETTE[OFF_WHITE]
    rose = PALETTE[DUSTY_ROSE]
    mag = PALETTE[MAGENTA]

    if paused:
        state_str = f"[{gold}]{_DIAMOND} Paused[/]"
    elif active:
        bright = frame % 60 < 30
        color = "#44cc44" if bright else "#228822"
        state_str = f"[{color}]{_DIAMOND} Active[/]"
    else:
        state_str = f"[dim]{_DIAMOND} Stopped[/]"

    uptime_str = _format_time(uptime_seconds)
    sim_str = f"[{gold}]On[/]" if simulate else "[dim]Off[/]"

    # Short mode label to fit panel
    mode_short = mode_label.replace("Display + System", "Disp+Sys")
    mode_short = mode_short.replace("Display Only", "Display")
    mode_short = mode_short.replace("System Only", "System")

    w = 24
    b = f"[{blue}]"
    top = f" {b}{_TL}{_H * w}{_TR}[/]"
    bot = f" {b}{_BL}{_H * w}{_BR}[/]"
    sep = f" {b}{_V}{_H * w}{_V}[/]"

    lines = [
        "",
        top,
        f" {b}{_V}[/][{gold} bold] {_DIAMOND} STATUS[/]",
        sep,
        f" {b}{_V}[/] [{white}]State:[/]  {state_str}",
        f" {b}{_V}[/] [{white}]Mode:[/]   [{rose}]{mode_short}[/]",
        f" {b}{_V}[/] [{white}]Uptime:[/] [{white}]{uptime_str}[/]",
        f" {b}{_V}[/] [{white}]Left:[/]   {remaining_str}",
        f" {b}{_V}[/] [{white}]Every:[/]  {interval}s",
        f" {b}{_V}[/] [{white}]Jiggle:[/] {sim_str}",
        bot,
    ]

    if progress_pct is not None:
        bar_w = 18
        filled = int(progress_pct / 100 * bar_w)
        bar = ""
        for i in range(bar_w):
            if i < filled:
                bar += f"[{mag}]\u2593[/]"
            else:
                bar += f"[{blue}]\u2591[/]"
        lines.append("")
        lines.append(f" {b}{_TL}{_H * w}{_TR}[/]")
        lines.append(f" {b}{_V}[/] {bar} [{white}]{progress_pct}%[/]")
        lines.append(f" {b}{_BL}{_H * w}{_BR}[/]")

    return "\n".join(lines)
