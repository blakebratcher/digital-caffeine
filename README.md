# Digital Caffeine ☕

> Keep your Windows machine awake - no more unwanted sleep.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Digital Caffeine prevents your Windows PC from going to sleep or turning off the display. It uses the native Windows `SetThreadExecutionState` API - no simulated mouse movements or keyboard input. Clean, reliable, and lightweight.

## Features

- **CLI mode** - Rich terminal interface with live status display
- **System tray mode** - Runs silently in the background with a coffee cup icon
- **Multiple modes** - Keep display on, prevent system sleep, or both
- **Timed sessions** - "Keep awake for 2 hours" with auto-stop
- **Configurable** - TOML config file for your preferred defaults
- **Zero input simulation** - Uses proper Windows API, not fake mouse moves

## Installation

```bash
pip install digital-caffeine
```

Or install from source:

```bash
git clone https://github.com/blakebratcher/digital-caffeine.git
cd digital-caffeine
pip install -e .
```

## Quick Start

```bash
# Keep awake (display + system) - CLI mode
caffeine start

# Keep awake for 2 hours
caffeine start --duration 2h

# Display only (prevent screen off, allow system sleep)
caffeine start --mode display

# Launch as system tray app
caffeine start --tray

# Custom refresh interval
caffeine start --interval 30
```

## CLI Usage

### `caffeine start`

Start keeping your machine awake.

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--mode` | `-m` | `all`, `display`, or `system` | `all` |
| `--interval` | `-i` | Refresh interval in seconds | `60` |
| `--duration` | `-d` | Auto-stop timer (`30m`, `2h`, `1h30m`) | indefinite |
| `--tray` | `-t` | Launch in system tray mode | off |

### `caffeine config`

Manage configuration.

```bash
caffeine config --show    # Display current config
caffeine config --init    # Create default config file
caffeine config --path    # Show config file location
```

### `caffeine version`

Show version info.

## System Tray Mode

Launch with `caffeine start --tray` for a background experience:

- Coffee cup icon in the system tray (filled = active, outline = paused)
- Right-click menu to change modes, pause/resume, or quit
- Notification when a timed session ends

## Configuration

Config file location: `~/.digital-caffeine/config.toml`

```toml
# Keep-awake mode: "all", "display", or "system"
mode = "all"

# Refresh interval in seconds
interval = 60

# Auto-stop duration (e.g. "2h", "30m")
# duration = "2h"
```

Generate a default config:

```bash
caffeine config --init
```

## How It Works

Digital Caffeine calls the Windows [`SetThreadExecutionState`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) API with the appropriate flags:

- `ES_DISPLAY_REQUIRED` - Prevents the display from turning off
- `ES_SYSTEM_REQUIRED` - Prevents the system from entering sleep
- `ES_CONTINUOUS` - Keeps the setting active until explicitly cleared

The flags are reasserted periodically (default every 60 seconds) as a safety measure. When you stop the program, it clears the flags so Windows resumes normal power management.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/
```

## License

MIT License. See [LICENSE](LICENSE) for details.
