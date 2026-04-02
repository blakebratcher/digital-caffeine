"""Tests for the Digital Caffeine CLI animations module."""

from __future__ import annotations

from digital_caffeine.animations import (
    BORDER_COLORS,
    PAUSED_QUIP,
    QUIPS,
    STEAM_FRAMES,
    get_border_color,
    get_cup_art,
    get_quip,
    get_steam_frame,
)

# -- Steam frame tests --


def test_steam_frames_has_four_frames() -> None:
    assert len(STEAM_FRAMES) == 4


def test_get_steam_frame_cycles_through_frames() -> None:
    for i in range(4):
        result = get_steam_frame(elapsed=i, paused=False)
        assert result == STEAM_FRAMES[i]


def test_get_steam_frame_wraps_around() -> None:
    assert get_steam_frame(elapsed=4, paused=False) == STEAM_FRAMES[0]
    assert get_steam_frame(elapsed=7, paused=False) == STEAM_FRAMES[3]


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
