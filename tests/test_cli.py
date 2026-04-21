"""Tests for the Digital Caffeine CLI module."""

from __future__ import annotations

from unittest.mock import patch

import click
import pytest
from click.testing import CliRunner

from digital_caffeine.cli import cli, parse_duration

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
