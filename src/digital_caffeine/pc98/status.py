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

# Box drawing characters for PC-98 aesthetic
_TL = "\u250c"  # top-left corner
_TR = "\u2510"  # top-right corner
_BL = "\u2514"  # bottom-left corner
_BR = "\u2518"  # bottom-right corner
_H = "\u2500"   # horizontal
_V = "\u2502"   # vertical
_DIAMOND = "\u25c6"  # filled diamond


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

    # State indicator with PC-98 style diamond
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

    w = 26  # inner width
    border = f"[{blue}]"
    header = f"  {border}{_TL}{_H * w}{_TR}[/]"
    footer = f"  {border}{_BL}{_H * w}{_BR}[/]"
    sep = f"  {border}{_V}[/]{border}{_H * w}[/]{border}{_V}[/]"

    def row(content: str) -> str:
        return f"  {border}{_V}[/] {content}"

    lines = [
        "",
        header,
        row(f"[{gold} bold]  STATUS[/]"),
        sep,
        row(f"[{white}]State:[/]    {state_str}"),
        row(f"[{white}]Mode:[/]     [{rose}]{mode_label}[/]"),
        row(f"[{white}]Uptime:[/]   [{white}]{uptime_str}[/]"),
        row(f"[{white}]Remain:[/]   {remaining_str}"),
        row(f"[{white}]Interval:[/] {interval}s"),
        row(f"[{white}]Simulate:[/] {sim_str}"),
        footer,
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
        lines.append(f"  {border}{_TL}{_H * w}{_TR}[/]")
        lines.append(row(f" {bar_chars} [{white}]{progress_pct}%[/]"))
        lines.append(f"  {border}{_BL}{_H * w}{_BR}[/]")

    return "\n".join(lines)
