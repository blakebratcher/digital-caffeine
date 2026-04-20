"""Tests for the minimal Digital Caffeine display."""

from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from digital_caffeine.animations import (
    QUIPS,
    _build_status_text,
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


def _render(text, width: int = 100) -> str:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=width, no_color=False)
    console.print(text)
    return buf.getvalue()


def test_build_status_text_includes_mode_phrase_and_elapsed() -> None:
    text = _build_status_text(
        spinner_frame="\u280b",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=65,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text)
    assert "caffeine" in rendered
    assert "keeping display awake" in rendered
    assert "1m 5s" in rendered


def test_build_status_text_duration_suffix_when_duration_set() -> None:
    text = _build_status_text(
        spinner_frame="\u280b",
        mode=Mode.DISPLAY_AND_SYSTEM,
        elapsed_seconds=60 * 38,
        duration_seconds=60 * 120,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text)
    assert "1h 22m / 2h 0m left" in rendered


def test_build_status_text_quit_hint_when_requested() -> None:
    text = _build_status_text(
        spinner_frame="\u280b",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    assert "q to quit" in _render(text)


def test_build_status_text_narrow_terminal_drops_suffixes() -> None:
    text = _build_status_text(
        spinner_frame="\u280b",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=3600,
        paused=False,
        width=40,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text, width=40)
    assert "q to quit" not in rendered
    assert "left" not in rendered
    # But mode phrase and elapsed are still there
    assert "keeping display awake" in rendered
    assert "30s" in rendered


def test_build_status_text_no_color_omits_ansi_codes() -> None:
    text = _build_status_text(
        spinner_frame="\u280b",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=False,
    )
    buf = StringIO()
    # no_color=False on the console itself so it WOULD emit ANSI if the Text
    # carried styles; we're asserting the Text has no styles to emit.
    Console(file=buf, force_terminal=True, width=100, no_color=False).print(text)
    assert "\x1b[" not in buf.getvalue()


def test_build_status_text_paused_uses_paused_phrase() -> None:
    text = _build_status_text(
        spinner_frame="\u2022",  # static frame for paused state
        mode=Mode.DISPLAY_AND_SYSTEM,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=True,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    assert "paused" in _render(text)
