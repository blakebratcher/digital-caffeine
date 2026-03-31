# Digital Caffeine - Development Guide

## Project Overview
Windows keep-awake utility with CLI and system tray modes. Uses `SetThreadExecutionState` API.

## Build & Run
```bash
pip install -e ".[dev]"    # Install in dev mode
caffeine start             # Run CLI mode
caffeine start --tray      # Run system tray mode
```

## Testing
```bash
pytest                     # Run all tests
pytest -x                  # Stop on first failure
ruff check src/ tests/     # Lint
```

## Architecture
- `src/digital_caffeine/engine.py` - Core keep-awake logic (CaffeineEngine)
- `src/digital_caffeine/cli.py` - Click CLI with Rich output
- `src/digital_caffeine/tray.py` - pystray system tray mode
- `src/digital_caffeine/config.py` - TOML config (~/.digital-caffeine/config.toml)
- `src/digital_caffeine/icons.py` - Programmatic icon generation with Pillow
- `src/digital_caffeine/constants.py` - Windows API constants

## Conventions
- Python 3.10+, type hints on all public APIs
- Use `ruff` for linting (line length 100)
- Tests in `tests/` using pytest + pytest-mock
