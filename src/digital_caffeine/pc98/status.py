"""PC-98 styled status panel for the right side of the display."""

from __future__ import annotations

from digital_caffeine.pc98.palette import GOLD, OFF_WHITE, PALETTE, STEEL_BLUE


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

    if paused:
        state_str = f"[{PALETTE[6]}]Paused[/]"
    elif active:
        bright = frame % 60 < 30
        color = "#44bb44" if bright else "#226622"
        state_str = f"[{color}]Active[/]"
    else:
        state_str = "[dim]Stopped[/]"

    uptime_str = _format_time(uptime_seconds)
    sim_str = f"[{gold}]On[/]" if simulate else "[dim]Off[/]"

    lines = [
        f"  [{gold}]STATUS[/]",
        f"  [{blue}]{'=' * 25}[/]",
        f"  [{white}]State:[/]    {state_str}",
        f"  [{white}]Mode:[/]     {mode_label}",
        f"  [{white}]Uptime:[/]   [{white}]{uptime_str}[/]",
        f"  [{white}]Remain:[/]   {remaining_str}",
        f"  [{white}]Interval:[/] {interval}s",
        f"  [{white}]Simulate:[/] {sim_str}",
    ]

    if progress_pct is not None:
        bar_w = 20
        filled = int(progress_pct / 100 * bar_w)
        bar = f"[{blue}]{'#' * filled}[/][dim]{'.' * (bar_w - filled)}[/]"
        lines.append(f"  [{blue}]{'=' * 25}[/]")
        lines.append(f"  {bar} {progress_pct}%")

    return "\n".join(lines)
