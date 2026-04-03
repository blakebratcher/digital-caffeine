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

# Ornate box drawing for PC-98 VN feel
_TL = "\u2554"  # double top-left
_TR = "\u2557"  # double top-right
_BL = "\u255a"  # double bottom-left
_BR = "\u255d"  # double bottom-right
_H = "\u2550"   # double horizontal
_V = "\u2551"   # double vertical
_DIAMOND = "\u25c6"
_DOT = "\u00b7"


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

    w = 26
    b = f"[{blue}]"
    d = f"[{rose}]{_DOT}[/]"  # decorative dot
    bar_top = f"  {b}{_TL}{_H}{_H}[/]{d}{b}{_H * (w - 4)}{_H}[/]{d}{b}{_H}{_TR}[/]"
    bar_bot = f"  {b}{_BL}{_H}{_H}[/]{d}{b}{_H * (w - 4)}{_H}[/]{d}{b}{_H}{_BR}[/]"

    lines = [
        "",
        bar_top,
        f"  {b}{_V}[/] [{gold} bold]{_DIAMOND} STATUS {_DIAMOND}[/]",
        f"  {b}{_V}[/]{b}{_H * w}{_V}[/]",
        f"  {b}{_V}[/] [{white}]State:[/]    {state_str}",
        f"  {b}{_V}[/] [{white}]Mode:[/]     [{rose}]{mode_label}[/]",
        f"  {b}{_V}[/] [{white}]Uptime:[/]   [{white}]{uptime_str}[/]",
        f"  {b}{_V}[/] [{white}]Remain:[/]   {remaining_str}",
        f"  {b}{_V}[/] [{white}]Interval:[/] {interval}s",
        f"  {b}{_V}[/] [{white}]Simulate:[/] {sim_str}",
        bar_bot,
    ]

    if progress_pct is not None:
        bar_w = 22
        filled = int(progress_pct / 100 * bar_w)
        bar_chars = ""
        for i in range(bar_w):
            if i < filled:
                bar_chars += f"[{mag}]\u2593[/]"
            else:
                bar_chars += f"[{blue}]\u2591[/]"
        lines.append("")
        lines.append(
            f"  {b}{_TL}{_H}[/][{rose}]{_DOT}[/]"
            f"{b}{_H * (w - 4)}[/]"
            f"[{rose}]{_DOT}[/]{b}{_H}{_TR}[/]"
        )
        lines.append(f"  {b}{_V}[/] {bar_chars} [{white}]{progress_pct}%[/]")
        lines.append(
            f"  {b}{_BL}{_H}[/][{rose}]{_DOT}[/]"
            f"{b}{_H * (w - 4)}[/]"
            f"[{rose}]{_DOT}[/]{b}{_H}{_BR}[/]"
        )

    return "\n".join(lines)
