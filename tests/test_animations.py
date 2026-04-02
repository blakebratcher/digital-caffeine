"""Tests for the Digital Caffeine CLI animations module."""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.panel import Panel

from digital_caffeine.animations import (
    BORDER_COLORS,
    PAUSED_QUIP,
    QUIPS,
    STEAM_FRAMES,
    build_animated_display,
    get_border_color,
    get_cup_art,
    get_quip,
    get_steam_frame,
)
from digital_caffeine.constants import Mode

# -- Steam frame tests --


def test_steam_frames_has_six_frames() -> None:
    assert len(STEAM_FRAMES) == 6


def test_get_steam_frame_cycles_through_frames() -> None:
    for i in range(6):
        result = get_steam_frame(elapsed=i, paused=False)
        assert result == STEAM_FRAMES[i]


def test_get_steam_frame_wraps_around() -> None:
    assert get_steam_frame(elapsed=6, paused=False) == STEAM_FRAMES[0]
    assert get_steam_frame(elapsed=11, paused=False) == STEAM_FRAMES[5]


def test_get_steam_frame_paused_returns_blank_lines() -> None:
    result = get_steam_frame(elapsed=0, paused=True)
    # Should be blank lines (no steam), same number of lines as a normal frame
    lines = result.split("\n")
    assert all(line.strip() == "" for line in lines)


# -- Cup art tests --


def test_get_cup_art_active_has_bold_fill() -> None:
    result = get_cup_art(paused=False)
    assert "\u2593" in result  # dark shade character


def test_get_cup_art_paused_has_dim_fill() -> None:
    result = get_cup_art(paused=True)
    assert "\u2591" in result  # light shade character


# -- Border color tests --


def test_border_colors_has_four_entries() -> None:
    assert len(BORDER_COLORS) == 4


def test_get_border_color_cycles() -> None:
    colors = [get_border_color(elapsed=i, paused=False) for i in range(8)]
    assert colors == BORDER_COLORS + BORDER_COLORS


def test_get_border_color_paused_returns_yellow() -> None:
    assert get_border_color(elapsed=0, paused=True) == "yellow"
    assert get_border_color(elapsed=3, paused=True) == "yellow"


# -- Quip tests --


def test_quips_has_at_least_ten() -> None:
    assert len(QUIPS) >= 10


def test_get_quip_rotates_every_eight_seconds() -> None:
    quip_0 = get_quip(elapsed=0, paused=False)
    quip_same = get_quip(elapsed=7, paused=False)
    quip_next = get_quip(elapsed=8, paused=False)
    assert quip_0 == quip_same  # same within 8s window
    assert quip_0 != quip_next  # different after 8s


def test_get_quip_wraps_around() -> None:
    cycle_length = len(QUIPS) * 8
    assert get_quip(elapsed=0, paused=False) == get_quip(elapsed=cycle_length, paused=False)


def test_get_quip_paused_returns_paused_quip() -> None:
    assert get_quip(elapsed=0, paused=True) == PAUSED_QUIP
    assert get_quip(elapsed=99, paused=True) == PAUSED_QUIP


# -- build_animated_display tests --


def test_build_animated_display_returns_panel() -> None:
    result = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert isinstance(result, Panel)


def test_build_animated_display_contains_status_info() -> None:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    panel = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=65,
        duration_seconds=3600,
        interval=60,
        paused=False,
        simulate=True,
    )
    console.print(panel)
    output = buf.getvalue()

    assert "Active" in output
    assert "Display + System" in output
    assert "00:01:05" in output  # uptime
    assert "00:58:55" in output  # remaining
    assert "60s" in output


def test_build_animated_display_paused_state() -> None:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    panel = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=10,
        duration_seconds=None,
        interval=60,
        paused=True,
        simulate=False,
    )
    console.print(panel)
    output = buf.getvalue()

    assert "Paused" in output
    assert "Gone cold" in output


def test_build_animated_display_border_color_changes() -> None:
    panel_0 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    panel_1 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=1,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    # Border styles should differ between frame 0 and frame 1
    assert panel_0.border_style != panel_1.border_style


def test_build_animated_display_quip_rotates() -> None:
    buf_0 = StringIO()
    console_0 = Console(file=buf_0, force_terminal=True, width=80)
    panel_0 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_0.print(panel_0)

    buf_8 = StringIO()
    console_8 = Console(file=buf_8, force_terminal=True, width=80)
    panel_8 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=8,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_8.print(panel_8)

    # The quip text should differ between second 0 and second 8
    assert buf_0.getvalue() != buf_8.getvalue()
