"""Minimal status-line display for the Digital Caffeine CLI.

Public surface:
    run_display(engine, mode, duration_seconds) -> None
    format_elapsed(seconds) -> str
"""

from __future__ import annotations

FPS = 2


def format_elapsed(seconds: int) -> str:
    """Format seconds as 'Xh Ym Zs' with leading zero segments dropped."""
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"
