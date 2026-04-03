"""PC-98 visual novel dialogue box with typewriter effect."""

from __future__ import annotations

from digital_caffeine.animations import PAUSED_QUIP, QUIPS
from digital_caffeine.pc98.palette import GOLD, OFF_WHITE, PALETTE

FPS = 24
_QUIP_INTERVAL = 12


def typewriter_text(quip: str, frame_in_quip: int) -> str:
    chars_to_show = min(len(quip), (frame_in_quip // 3) + 1)
    if chars_to_show < len(quip):
        cursor = "\u2588" if (frame_in_quip % 18) < 9 else " "
        return quip[:chars_to_show] + cursor
    return quip


def get_current_quip(frame: int, *, paused: bool) -> str:
    if paused:
        return PAUSED_QUIP
    frames_per_quip = _QUIP_INTERVAL * FPS
    quip_idx = (frame // frames_per_quip) % len(QUIPS)
    quip = QUIPS[quip_idx]
    frame_in_quip = frame % frames_per_quip
    return typewriter_text(quip, frame_in_quip)


def format_dialogue_box(frame: int, *, paused: bool) -> str:
    gold = PALETTE[GOLD]
    white = PALETTE[OFF_WHITE]
    quip = get_current_quip(frame, paused=paused)
    label = f"[{gold}][ CAFFEINE ][/]"
    text = f"[{white}]{quip}[/]"
    return f"  {label}\n  {text}"
