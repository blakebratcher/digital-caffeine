"""Tests for the Digital Caffeine configuration module."""

from __future__ import annotations

import pytest

from digital_caffeine.config import (
    DEFAULT_CONFIG,
    create_default_config,
    load_config,
    resolve_mode,
    save_config,
)
from digital_caffeine.constants import Mode

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


@pytest.fixture()
def _patch_config_paths(tmp_path, monkeypatch):
    """Redirect CONFIG_DIR and CONFIG_FILE to a temporary directory."""
    config_dir = tmp_path / ".digital-caffeine"
    config_file = config_dir / "config.toml"
    monkeypatch.setattr("digital_caffeine.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("digital_caffeine.config.CONFIG_FILE", config_file)
    return config_dir, config_file


# --------------------------------------------------------------------------- #
# DEFAULT_CONFIG
# --------------------------------------------------------------------------- #


def test_default_config_values():
    """DEFAULT_CONFIG contains the expected keys and values."""
    assert DEFAULT_CONFIG["mode"] == "all"
    assert DEFAULT_CONFIG["interval"] == 60
    assert DEFAULT_CONFIG["duration"] is None
    assert set(DEFAULT_CONFIG.keys()) == {"mode", "interval", "duration"}


# --------------------------------------------------------------------------- #
# load_config
# --------------------------------------------------------------------------- #


def test_load_config_no_file(_patch_config_paths):
    """load_config returns defaults when no config file exists."""
    result = load_config()
    assert result == DEFAULT_CONFIG
    # Must be a fresh copy, not the same object
    assert result is not DEFAULT_CONFIG


def test_load_config_from_file(_patch_config_paths):
    """load_config reads values from a valid TOML file."""
    config_dir, config_file = _patch_config_paths
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text(
        'mode = "display"\ninterval = 120\n',
        encoding="utf-8",
    )

    result = load_config()
    assert result["mode"] == "display"
    assert result["interval"] == 120
    # duration should come from DEFAULT_CONFIG since it is not in the file
    assert result["duration"] is None


def test_load_config_merges_defaults(_patch_config_paths):
    """A partial TOML file gets missing keys filled in from defaults."""
    config_dir, config_file = _patch_config_paths
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file.write_text('mode = "system"\n', encoding="utf-8")

    result = load_config()
    assert result["mode"] == "system"
    # These should be inherited from DEFAULT_CONFIG
    assert result["interval"] == 60
    assert result["duration"] is None


# --------------------------------------------------------------------------- #
# save_config
# --------------------------------------------------------------------------- #


def test_save_config_creates_file(_patch_config_paths):
    """save_config creates the config file and its parent directory."""
    _config_dir, config_file = _patch_config_paths

    path = save_config({"mode": "all", "interval": 60, "duration": None})

    assert path == config_file
    assert config_file.exists()


def test_save_config_none_values_commented(_patch_config_paths):
    """None values are written as commented-out lines ('# key =')."""
    _config_dir, config_file = _patch_config_paths

    save_config({"mode": "all", "interval": 60, "duration": None})
    content = config_file.read_text(encoding="utf-8")

    # duration should be commented out
    assert "# duration =" in content
    # mode and interval should NOT be commented
    assert 'mode = "all"' in content
    assert "interval = 60" in content


# --------------------------------------------------------------------------- #
# create_default_config
# --------------------------------------------------------------------------- #


def test_create_default_config(_patch_config_paths):
    """create_default_config writes the template with expected content."""
    _config_dir, config_file = _patch_config_paths

    path = create_default_config()

    assert path == config_file
    assert config_file.exists()

    content = config_file.read_text(encoding="utf-8")
    assert "Digital Caffeine Configuration" in content
    assert 'mode = "all"' in content
    assert "interval = 60" in content
    # duration should appear as a commented-out example
    assert "# duration" in content


# --------------------------------------------------------------------------- #
# resolve_mode
# --------------------------------------------------------------------------- #


def test_resolve_mode_all():
    assert resolve_mode("all") is Mode.DISPLAY_AND_SYSTEM


def test_resolve_mode_display():
    assert resolve_mode("display") is Mode.DISPLAY_ONLY


def test_resolve_mode_system():
    assert resolve_mode("system") is Mode.SYSTEM_ONLY


def test_resolve_mode_case_insensitive():
    """Mode strings should be matched regardless of case."""
    assert resolve_mode("ALL") is Mode.DISPLAY_AND_SYSTEM
    assert resolve_mode("Display") is Mode.DISPLAY_ONLY
    assert resolve_mode("SYSTEM") is Mode.SYSTEM_ONLY


def test_resolve_mode_invalid_raises():
    """An unrecognised mode string raises ValueError."""
    with pytest.raises(ValueError, match="Unknown mode"):
        resolve_mode("invalid")
