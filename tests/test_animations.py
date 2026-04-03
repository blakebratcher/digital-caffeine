"""Tests for the Digital Caffeine CLI animations module."""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.panel import Panel

from digital_caffeine.animations import (
    BORDER_COLORS,
    FPS,
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


def test_steam_frames_are_generated() -> None:
    assert len(STEAM_FRAMES) == 24


def test_get_steam_frame_cycles() -> None:
    first = get_steam_frame(frame=0, paused=False)
    # Steam advances at half FPS, so full cycle is len * 2 frames
    wrapped = get_steam_frame(frame=len(STEAM_FRAMES) * 2, paused=False)
    assert first == wrapped


def test_get_steam_frame_has_five_lines() -> None:
    result = get_steam_frame(frame=0, paused=False)
    assert len(result.split("\n")) == 5


def test_get_steam_frame_paused_returns_blank_lines() -> None:
    result = get_steam_frame(frame=0, paused=True)
    lines = result.split("\n")
    assert len(lines) == 5
    assert all(line.strip() == "" for line in lines)


# -- Cup art tests --


def test_get_cup_art_active_has_fill() -> None:
    result = get_cup_art(frame=0, paused=False)
    assert "\u2593" in result


def test_get_cup_art_paused_has_dim_fill() -> None:
    result = get_cup_art(frame=0, paused=True)
    assert "\u2591" in result


def test_get_cup_art_active_has_seven_lines() -> None:
    result = get_cup_art(frame=0, paused=False)
    assert len(result.split("\n")) == 7


def test_get_cup_art_surface_animates() -> None:
    art_0 = get_cup_art(frame=0, paused=False)
    art_2 = get_cup_art(frame=2, paused=False)
    assert art_0 != art_2


# -- Border color tests --


def test_border_colors_has_smooth_steps() -> None:
    assert len(BORDER_COLORS) == 32
    assert all(c.startswith("#") for c in BORDER_COLORS)


def test_get_border_color_cycles() -> None:
    colors = [get_border_color(frame=i, paused=False) for i in range(32)]
    assert colors == BORDER_COLORS
    assert get_border_color(frame=32, paused=False) == BORDER_COLORS[0]


def test_get_border_color_paused_returns_yellow() -> None:
    assert get_border_color(frame=0, paused=True) == "yellow"
    assert get_border_color(frame=99, paused=True) == "yellow"


# -- Quip tests --


def test_quips_has_many_entries() -> None:
    assert len(QUIPS) >= 100


def test_get_quip_rotates() -> None:
    frames_per_quip = 12 * FPS  # 12 seconds per quip at 24 FPS
    quip_a = get_quip(frame=frames_per_quip - 1, paused=False)
    quip_b = get_quip(frame=2 * frames_per_quip - 1, paused=False)
    assert quip_a != quip_b


def test_get_quip_typewriter_effect() -> None:
    partial = get_quip(frame=0, paused=False)
    full = get_quip(frame=12 * FPS - 1, paused=False)
    assert len(partial) < len(full)
    assert full.startswith(partial[:1])


def test_get_quip_wraps_around() -> None:
    cycle_length = len(QUIPS) * 12 * FPS
    end = 12 * FPS - 1
    assert get_quip(frame=end, paused=False) == get_quip(
        frame=cycle_length + end, paused=False
    )


def test_get_quip_paused_returns_paused_quip() -> None:
    assert get_quip(frame=0, paused=True) == PAUSED_QUIP
    assert get_quip(frame=99, paused=True) == PAUSED_QUIP


# -- build_animated_display tests --


def test_build_animated_display_returns_panel() -> None:
    result = build_animated_display(
        frame=0,
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
    console = Console(file=buf, force_terminal=True, width=90)
    panel = build_animated_display(
        frame=0,
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
    assert "00:01:05" in output
    assert "00:58:55" in output
    assert "60s" in output


def test_build_animated_display_paused_state() -> None:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=90)
    panel = build_animated_display(
        frame=0,
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
        frame=0,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    panel_1 = build_animated_display(
        frame=1,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert panel_0.border_style != panel_1.border_style


def test_build_animated_display_quip_rotates() -> None:
    buf_0 = StringIO()
    console_0 = Console(file=buf_0, force_terminal=True, width=90)
    panel_0 = build_animated_display(
        frame=0,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_0.print(panel_0)

    buf_8 = StringIO()
    console_8 = Console(file=buf_8, force_terminal=True, width=90)
    panel_8 = build_animated_display(
        frame=12 * FPS,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=12,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_8.print(panel_8)

    assert buf_0.getvalue() != buf_8.getvalue()
