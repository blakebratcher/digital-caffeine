"""Configuration management for Digital Caffeine.

Handles loading, saving, and creating user configuration stored as TOML
in ~/.digital-caffeine/config.toml.
"""

from __future__ import annotations

from pathlib import Path

from digital_caffeine.constants import Mode

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

CONFIG_DIR: Path = Path.home() / ".digital-caffeine"
CONFIG_FILE: Path = CONFIG_DIR / "config.toml"


def get_config_dir() -> Path:
    """Return the configuration directory path."""
    return CONFIG_DIR


def get_config_path() -> Path:
    """Return the configuration file path."""
    return CONFIG_FILE


# --------------------------------------------------------------------------- #
# Defaults
# --------------------------------------------------------------------------- #

DEFAULT_CONFIG: dict[str, object] = {
    "mode": "all",
    "interval": 60,
    "duration": None,
    "simulate": False,
}

# --------------------------------------------------------------------------- #
# Mode resolution
# --------------------------------------------------------------------------- #

_MODE_MAP: dict[str, Mode] = {
    "all": Mode.DISPLAY_AND_SYSTEM,
    "display": Mode.DISPLAY_ONLY,
    "system": Mode.SYSTEM_ONLY,
}


def resolve_mode(mode_str: str) -> Mode:
    """Convert a CLI mode string to a Mode enum value.

    Accepted strings: "all", "display", "system".

    Raises
    ------
    ValueError
        If *mode_str* is not a recognised mode name.
    """
    key = mode_str.strip().lower()
    if key not in _MODE_MAP:
        valid = ", ".join(sorted(_MODE_MAP))
        raise ValueError(
            f"Unknown mode {mode_str!r}. Valid options: {valid}"
        )
    return _MODE_MAP[key]


# --------------------------------------------------------------------------- #
# TOML reading
# --------------------------------------------------------------------------- #

def _load_toml(path: Path) -> dict[str, object]:
    """Read a TOML file and return its contents as a dict.

    Uses ``tomllib`` (Python 3.11+) with a fallback to the third-party
    ``tomli`` package for Python 3.10.
    """
    try:
        import tomllib  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]

    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config() -> dict[str, object]:
    """Load configuration from the TOML file.

    If the file does not exist the default configuration is returned.
    Any keys missing from the file are filled in from ``DEFAULT_CONFIG``.
    """
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)

    data = _load_toml(CONFIG_FILE)

    # Merge - defaults first, then overwrite with file values.
    merged: dict[str, object] = dict(DEFAULT_CONFIG)
    merged.update(data)
    return merged


# --------------------------------------------------------------------------- #
# TOML writing
# --------------------------------------------------------------------------- #

def _format_toml_value(value: object) -> str:
    """Format a single Python value as a TOML literal."""
    if value is None:
        # TOML has no null - represent as a commented-out key upstream.
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return f'"{value}"'
    raise TypeError(f"Unsupported TOML value type: {type(value)}")


def save_config(config: dict[str, object]) -> Path:
    """Save a configuration dict to the TOML file.

    Creates the configuration directory if it does not already exist.
    Returns the path that was written to.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for key, value in config.items():
        if value is None:
            # Write None values as commented-out entries.
            lines.append(f"# {key} =")
        else:
            lines.append(f"{key} = {_format_toml_value(value)}")

    CONFIG_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return CONFIG_FILE


# --------------------------------------------------------------------------- #
# Default config creation
# --------------------------------------------------------------------------- #

_DEFAULT_CONFIG_TEMPLATE = """\
# Digital Caffeine Configuration

# Keep-awake mode: "all" (display + system), "display", or "system"
mode = "all"

# How often to reassert keep-awake flags (seconds)
interval = 60

# Auto-stop after duration (e.g. "2h", "30m", "1h30m")
# Leave empty or remove for indefinite
# duration = "2h"

# Simulate mouse input to keep apps like Teams/Slack active
simulate = false
"""


def create_default_config() -> Path:
    """Create the configuration file populated with defaults and helpful comments.

    Creates the configuration directory if it does not already exist.
    Returns the path that was written to.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(_DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")
    return CONFIG_FILE
