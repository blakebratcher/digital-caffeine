"""Minimal status-line display for the Digital Caffeine CLI.

Public surface:
    run_display(engine, mode, duration_seconds) -> None
    format_elapsed(seconds) -> str
"""

from __future__ import annotations

from digital_caffeine.constants import Mode

FPS = 2

_MODE_PHRASES: dict[Mode, str] = {
    Mode.DISPLAY_ONLY: "keeping display awake",
    Mode.SYSTEM_ONLY: "keeping system awake",
    Mode.DISPLAY_AND_SYSTEM: "keeping display + system awake",
}

_PAUSED_PHRASE = "paused"


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


def _format_duration(seconds: int) -> str:
    """Format seconds as 'Xh Ym' (no seconds). Clamps negatives to zero."""
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _mode_phrase(mode: Mode, paused: bool) -> str:
    """Return the descriptive phrase for the current engine state."""
    if paused:
        return _PAUSED_PHRASE
    return _MODE_PHRASES[mode]
