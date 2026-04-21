# Digital Caffeine - Development Guide

## Project Overview
Windows keep-awake utility with CLI and system tray modes. Uses `SetThreadExecutionState` API.

## Build & Run
```bash
pip install -e ".[dev]"           # Install in dev mode with test/lint deps
caffeine start                    # CLI mode (animated terminal UI)
caffeine start --tray             # System tray mode
python -m digital_caffeine        # Alternative entry point (via __main__.py)
```

## Testing
```bash
pytest                     # Run all tests
pytest -x                  # Stop on first failure
ruff check src/ tests/     # Lint
```

## CLI Commands
```bash
caffeine start                    # Keep awake indefinitely (display+system)
caffeine start --mode display     # Keep only display awake
caffeine start --duration 2h30m   # Run for a set duration (supports: 30s, 5m, 2h, 1h30m15s)
caffeine start --simulate         # Enable mouse jiggle for Teams/Slack (NOT a dry run)
caffeine start --tray             # Run as system tray icon
caffeine config --show            # Print current config
caffeine config --init            # Create default config file
caffeine config --path            # Print config file path
caffeine version                  # Print version
```

## Architecture
- `src/digital_caffeine/__init__.py` - Package root, defines `__version__`
- `src/digital_caffeine/__main__.py` - Enables `python -m digital_caffeine`
- `src/digital_caffeine/engine.py` - Core keep-awake logic (CaffeineEngine), thread-safe with pause/resume
- `src/digital_caffeine/cli.py` - Click CLI group with `start`, `config`, `version` subcommands
- `src/digital_caffeine/animations.py` - Minimal single-line status display via `run_display` (spinner + mode phrase + elapsed + optional duration suffix), rotating quip pool, TTY vs non-TTY split
- `src/digital_caffeine/tray.py` - pystray system tray mode (TrayApp class)
- `src/digital_caffeine/config.py` - TOML config at `~/.digital-caffeine/config.toml`
- `src/digital_caffeine/icons.py` - Programmatic icon generation with Pillow (active/paused/stopped states)
- `src/digital_caffeine/constants.py` - Windows API constants and `Mode` enum

## Config
Config lives at `~/.digital-caffeine/config.toml`. Precedence: **CLI flags > config file > defaults**.

Defaults: `mode = "all"`, `interval = 60`, `duration = None`, `simulate = false`.

## Testing Patterns
- **Windows API is always mocked**: `test_engine.py` uses an `autouse` fixture that patches `SetThreadExecutionState` globally. Target path: `digital_caffeine.engine.ctypes.windll.kernel32.SetThreadExecutionState`.
- **Config tests redirect paths**: Use `monkeypatch` to point `CONFIG_DIR`/`CONFIG_FILE` to `tmp_path`.
- **CLI tests**: Use Click's `CliRunner` for command invocation.

## Conventions
- Python 3.10+, type hints on all public APIs
- Use `ruff` for linting (line length 100)
- Tests in `tests/` using pytest + pytest-mock

## Gotchas
- **Windows-only**: Engine uses `ctypes.windll.kernel32.SetThreadExecutionState`. Use `--simulate` on the CLI, but note the engine itself will still call the API. Tests mock it automatically.
- **`--simulate` is NOT a dry run**: It enables a 1px mouse jiggle (right then left) via `SendInput` to fool presence detection in Teams/Slack/Zoom. The engine still calls `SetThreadExecutionState` either way.
- **Python 3.10 needs `tomli`**: `config.py` falls back from `tomllib` (3.11+) to `tomli`. Not in `dependencies` - users on 3.10 must install it manually or config loading will fail.
- **Animation at 10 FPS**: `animations.py` drives `rich.live.Live` at 10 FPS. The `FPS` constant controls refresh rate.
- **TTY vs non-TTY in `run_display`**: On a TTY it runs a Rich `Live` redraw loop with `q`-to-quit (via `msvcrt`). When stdout is piped/redirected it prints one status line and sleeps until the engine stops, so log output stays clean.
- **Duration expiry in tray mode**: Engine fires an `on_stop` callback on a separate daemon thread to avoid self-join deadlock.
