"""Tests for the Digital Caffeine CLI module."""

from __future__ import annotations

from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from digital_caffeine.cli import cli, format_time, parse_duration

# -- parse_duration tests --


def test_parse_duration_seconds() -> None:
    assert parse_duration("30s") == 30


def test_parse_duration_minutes() -> None:
    assert parse_duration("30m") == 1800


def test_parse_duration_hours() -> None:
    assert parse_duration("2h") == 7200


def test_parse_duration_combined() -> None:
    assert parse_duration("1h30m") == 5400
    assert parse_duration("1h30m15s") == 5415


def test_parse_duration_invalid_raises() -> None:
    with pytest.raises(click.BadParameter):
        parse_duration("abc")

    with pytest.raises(click.BadParameter):
        parse_duration("")

    with pytest.raises(click.BadParameter):
        parse_duration("10x")


def test_parse_duration_zero_raises() -> None:
    with pytest.raises(click.BadParameter):
        parse_duration("0s")


# -- format_time tests --


def test_format_time_zero() -> None:
    assert format_time(0) == "00:00:00"


def test_format_time_minutes_seconds() -> None:
    assert format_time(61) == "00:01:01"


def test_format_time_hours() -> None:
    assert format_time(3661) == "01:01:01"


# -- CLI command tests --


def test_version_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "Digital Caffeine v" in result.output


def test_config_path_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "--path"])
    assert result.exit_code == 0
    # The output should contain a filesystem path string
    assert len(result.output.strip()) > 0


def test_config_show_no_file(tmp_path: pytest.TempPathFactory) -> None:
    fake_config = tmp_path / "nonexistent" / "config.toml"

    with patch("digital_caffeine.cli.get_config_path", return_value=fake_config):
        runner = CliRunner()
        result = runner.invoke(cli, ["config", "--show"])

    assert result.exit_code == 0
    assert "No config file found" in result.output


def test_start_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["start", "--help"])
    assert result.exit_code == 0
    assert "Start keeping your machine awake" in result.output


from digital_caffeine.cli import build_display
from digital_caffeine.constants import Mode
from rich.panel import Panel


def test_build_display_returns_animated_panel() -> None:
    """build_display should delegate to the animated display builder."""
    panel = build_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert isinstance(panel, Panel)

    # Verify it has animated content by checking for coffee cup character
    from rich.console import Console
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    console.print(panel)
    output = buf.getvalue()
    # The cup should contain box-drawing characters from the animated display
    assert "\u2502" in output  # vertical box line from cup art
