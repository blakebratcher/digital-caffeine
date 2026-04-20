"""Tests for the minimal Digital Caffeine display."""

from __future__ import annotations

import pytest

from digital_caffeine.animations import format_elapsed


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
