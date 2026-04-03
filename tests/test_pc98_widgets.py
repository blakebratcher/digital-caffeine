"""Tests for PC-98 status panel and dialogue box widgets."""

from digital_caffeine.pc98.dialogue import (
    get_current_quip,
    typewriter_text,
)
from digital_caffeine.pc98.status import format_status_text


class TestFormatStatusText:
    def test_returns_string(self):
        result = format_status_text(
            active=True, paused=False, mode_label="Display + System",
            uptime_seconds=60, remaining_str="Indefinite",
            interval=60, simulate=False, frame=0,
        )
        assert isinstance(result, str)

    def test_contains_status_fields(self):
        result = format_status_text(
            active=True, paused=False, mode_label="Display + System",
            uptime_seconds=3661, remaining_str="Indefinite",
            interval=60, simulate=False, frame=0,
        )
        assert "STATUS" in result
        assert "Display + System" in result
        assert "01:01:01" in result
        assert "Indefinite" in result

    def test_paused_shows_paused(self):
        result = format_status_text(
            active=True, paused=True, mode_label="Display + System",
            uptime_seconds=0, remaining_str="Indefinite",
            interval=60, simulate=False, frame=0,
        )
        assert "Paused" in result

    def test_simulate_on(self):
        result = format_status_text(
            active=True, paused=False, mode_label="Display + System",
            uptime_seconds=0, remaining_str="Indefinite",
            interval=60, simulate=True, frame=0,
        )
        assert "On" in result


class TestTypewriterText:
    def test_reveals_characters_over_frames(self):
        t0 = typewriter_text("Hello World", frame_in_quip=0)
        t9 = typewriter_text("Hello World", frame_in_quip=30)
        assert len(t0) < len(t9) or t0 == t9

    def test_first_frame_shows_first_char(self):
        result = typewriter_text("Hello", frame_in_quip=0)
        assert result.startswith("H")

    def test_fully_revealed(self):
        result = typewriter_text("Hi", frame_in_quip=100)
        assert "Hi" in result

    def test_cursor_present_while_typing(self):
        result = typewriter_text("Hello World Test", frame_in_quip=3)
        assert len(result) > 1


class TestGetCurrentQuip:
    def test_returns_string(self):
        result = get_current_quip(frame=0, paused=False)
        assert isinstance(result, str)

    def test_paused_returns_paused_quip(self):
        result = get_current_quip(frame=0, paused=True)
        assert "cold" in result.lower() or "resume" in result.lower()

    def test_different_frames_eventually_differ(self):
        quips = set()
        for f in range(0, 10000, 288):
            quips.add(get_current_quip(frame=f, paused=False))
        assert len(quips) > 1
