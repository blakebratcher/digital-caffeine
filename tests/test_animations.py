"""Tests for the minimal Digital Caffeine display."""

from __future__ import annotations

import pytest

from digital_caffeine.animations import _format_duration, _mode_phrase, format_elapsed
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
