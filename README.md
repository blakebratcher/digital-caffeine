# Digital Caffeine

```
         )  )
        (  (             Your PC called.
         )  )            It said it's tired.
      +-----------+      
      | ......... |~\    We said no.
      | ......... | |    
      | ......... |~/    
      +-----------+      
     =================   
```

> Keep your Windows machine aggressively, unreasonably awake.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## So what is this

You know that thing where you step away from your desk for 45 seconds to refill your water and Windows decides that's a great time to lock the screen? And then you have to type your 47-character enterprise password again while your boss watches? Yeah.

Digital Caffeine tells your PC to knock it off. It uses the Windows `SetThreadExecutionState` API to prevent sleep and screen dimming. No mouse jiggling, no fake keypresses, just the actual API that Windows provides for exactly this purpose. We don't know why more tools don't just do this.

## What you get

The CLI mode gives you a live dashboard with an animated coffee cup, steam that actually moves, a border that pulses through different colors, and a rotation of coffee puns at the bottom. Is this necessary? No. Did we do it anyway? Obviously.

There's also a system tray mode if you'd rather it just sit in the corner and do its job quietly. Coffee cup icon, right-click menu, notifications when a timed session ends.

Other stuff it does:
- Three keep-awake modes (display only, system only, or both at once)
- Timed sessions, so you can say "2 hours" and it actually stops
- A `--simulate` flag that wiggles the mouse 1px each cycle so Teams thinks you're still there
- TOML config file for saving your preferred defaults

## Install

```bash
pip install digital-caffeine
```

Or clone it and install from source:

```bash
git clone https://github.com/blakebratcher/digital-caffeine.git
cd digital-caffeine
pip install -e .
```

## Usage

```bash
# just keep everything awake
caffeine start

# keep awake for 2 hours then stop
caffeine start --duration 2h

# only prevent the screen from turning off
caffeine start --mode display

# look busy on Teams while you "think strategically"
caffeine start --simulate

# system tray mode
caffeine start --tray

# go nuts
caffeine start --simulate --duration 8h --mode all
```

## What the CLI looks like

When you run `caffeine start`, you get this:

```
  +-------------------------------------------------------------+
  |                    Digital Caffeine                          |
  |                                                             |
  |          )  )           Status:         Active              |
  |         (  (            Mode:           Display + System    |
  |          )  )           Uptime:         00:05:23            |
  |       +-----------+     Time remaining: 01:54:37            |
  |       | ......... |~\   Interval:       60s                 |
  |       | ......... | |   Simulate:       On                  |
  |       | ......... |~/                                       |
  |       +-----------+                                         |
  |      =================                                     |
  |                                                             |
  |    Espresso yourself freely                                 |
  |                                                             |
  |    Press Ctrl+C to stop                                     |
  +-------------------------------------------------------------+
```

The steam cycles through frames, the border shifts color, and the puns rotate every 8 seconds. Nobody asked for this.

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--mode` | `-m` | `all`, `display`, or `system` | `all` |
| `--interval` | `-i` | How often to reassert flags, in seconds | `60` |
| `--duration` | `-d` | Stop after this long (`30m`, `2h`, `1h30m`) | runs forever |
| `--tray` | `-t` | Launch in system tray instead | off |
| `--simulate` | `-s` | Wiggle mouse for Teams/Slack | off |

## System tray mode

```bash
caffeine start --tray
```

Puts a coffee cup in the system tray. Filled cup means it's working, outline means it's paused. Right-click to switch modes, pause, toggle simulate, or quit.

## Configuration

```bash
caffeine config --init    # Create a default config file
caffeine config --show    # See what's in there
caffeine config --path    # Print where the config file lives
```

Config file goes in `~/.digital-caffeine/config.toml`:

```toml
# Keep-awake mode: "all", "display", or "system"
mode = "all"

# Refresh interval in seconds
interval = 60

# Auto-stop duration (e.g. "2h", "30m")
# duration = "2h"

# Simulate mouse input to keep Teams/Slack active
simulate = false
```

## How it actually works

```
  Your PC:  "I'm sleepy..."
  Caffeine: "SetThreadExecutionState(ES_CONTINUOUS | ES_DISPLAY_REQUIRED)"
  Your PC:  "I've never been more awake in my life."
```

It calls the Windows [`SetThreadExecutionState`](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate) API with these flags:

| Flag | What it prevents |
|------|-----------------|
| `ES_DISPLAY_REQUIRED` | Screen turning off |
| `ES_SYSTEM_REQUIRED` | System going to sleep |
| `ES_CONTINUOUS` | Keeps the flags active until explicitly cleared |

Flags get reasserted every 60 seconds (configurable) as a safety net. When you stop the program, it clears everything and Windows goes back to normal power management.

The `--simulate` flag adds a 1px mouse move (right, then back left) each cycle. You can't see it, but Teams can. Go make that sandwich.

## Development

```bash
pip install -e ".[dev]"    # Dev dependencies
pytest                     # Run tests
pytest -x                  # Stop on first failure
ruff check src/ tests/     # Lint
```

## License

MIT. See [LICENSE](LICENSE).

Do whatever you want with it.
