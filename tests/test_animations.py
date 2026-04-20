"""Tests for the minimal Digital Caffeine display."""

from __future__ import annotations

import pytest

from digital_caffeine.animations import (
    QUIPS,
    _format_duration,
    _mode_phrase,
    _pick_quip,
    format_elapsed,
)
from digital_caffeine.constants import Mode


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0s"),
        (5, "5s"),
        (59, "59s"),
        (60, "1m 0s"),
        (61, "1m 1s"),
        (3599, "59m 59s"),
        (3600, "1h 0m 0s"),
        (3661, "1h 1m 1s"),
        (7385, "2h 3m 5s"),
    ],
)
def test_format_elapsed_boundary_cases(seconds: int, expected: str) -> None:
    assert format_elapsed(seconds) == expected


def test_format_elapsed_negative_clamps_to_zero() -> None:
    assert format_elapsed(-10) == "0s"


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0m"),
        (60, "1m"),
        (1800, "30m"),
        (3600, "1h 0m"),
        (5400, "1h 30m"),
        (7200, "2h 0m"),
        (9000, "2h 30m"),
    ],
)
def test_format_duration_omits_seconds(seconds: int, expected: str) -> None:
    assert _format_duration(seconds) == expected


def test_mode_phrase_display_only() -> None:
    assert _mode_phrase(Mode.DISPLAY_ONLY, paused=False) == "keeping display awake"


def test_mode_phrase_system_only() -> None:
    assert _mode_phrase(Mode.SYSTEM_ONLY, paused=False) == "keeping system awake"


def test_mode_phrase_display_and_system() -> None:
    assert (
        _mode_phrase(Mode.DISPLAY_AND_SYSTEM, paused=False)
        == "keeping display + system awake"
    )


def test_mode_phrase_paused_overrides_mode() -> None:
    assert _mode_phrase(Mode.DISPLAY_AND_SYSTEM, paused=True) == "paused"
    assert _mode_phrase(Mode.DISPLAY_ONLY, paused=True) == "paused"
    assert _mode_phrase(Mode.SYSTEM_ONLY, paused=True) == "paused"


def test_quips_pool_has_at_least_one_hundred() -> None:
    assert len(QUIPS) >= 100


def test_pick_quip_is_empty_during_startup_window() -> None:
    for elapsed in range(5):
        assert _pick_quip(elapsed_seconds=elapsed, seed=42) == ""


def test_pick_quip_returns_a_pool_member_after_startup() -> None:
    quip = _pick_quip(elapsed_seconds=5, seed=42)
    assert quip in QUIPS


def test_pick_quip_changes_after_rotation_interval() -> None:
    # Rotation is 90 seconds. Two elapsed values that straddle the boundary
    # should (with overwhelming probability) yield different quips. Using
    # a fixed seed makes this deterministic.
    a = _pick_quip(elapsed_seconds=5, seed=42)
    b = _pick_quip(elapsed_seconds=5 + 90, seed=42)
    assert a != b


def test_pick_quip_same_within_rotation_window() -> None:
    a = _pick_quip(elapsed_seconds=5, seed=42)
    b = _pick_quip(elapsed_seconds=5 + 89, seed=42)
    assert a == b
