# CLI Animations Design

## Overview

Add fun, coffee-themed animations to the CLI live display while Digital Caffeine is running. The animations combine coffee aesthetics (steam, cup art), ambient chill (pulsing border), and playful personality (rotating quips).

## Coffee Cup ASCII Art & Steam Animation

A fixed ASCII coffee cup (~5 lines tall) displayed on the left side of the panel:

```
       ~ ~
      ( _ )
   +-------+ |
   |#######| |
   +-------+ /
```

Steam frames cycle each second through 4 frames. The steam characters shift upward and morph between `~`, curvy, and `( )` shapes, creating a rising-steam illusion. When paused, the steam disappears and the cup liquid dims (cold coffee).

The cup is approximately 15 characters wide.

## Layout

Two-column layout inside the existing Rich Panel:

- Left column: coffee cup with animated steam (fixed ~18 chars wide)
- Right column: status info (same fields as current - status, mode, uptime, time remaining, interval, simulate)

The panel title remains "Digital Caffeine" with a coffee emoji. The border color gently pulses by cycling through cyan/teal shades each second for an ambient breathing feel.

## Rotating Quips

A line at the bottom of the panel (above "Press Ctrl+C to stop") shows a rotating coffee-themed message that changes every ~8 seconds. Pool of 10-15 quips such as:

- "Brewing productivity..."
- "Your PC is caffeinated"
- "Sleep is for the weak (and not this PC)"
- "Keeping things percolating..."
- "Another cup? Don't mind if I do"
- "Drip, drip, drip... staying awake"
- "Freshly brewed and wide awake"
- "No decaf allowed here"

Displayed in dim italic styling so it doesn't compete with status info.

When paused, the quip switches to a fixed message like "Gone cold... resume to reheat" in yellow dim text.

## Paused State

When the engine is paused, the display changes to reflect "cold coffee":

- Steam disappears (replaced with blank lines)
- Cup liquid dims (lighter fill characters instead of bold)
- Border color switches to yellow
- Quip becomes a fixed cold-coffee message

## Implementation

### New file: `src/digital_caffeine/animations.py`

All animation state and rendering logic:

- `STEAM_FRAMES`: list of 4 steam frame strings
- `BORDER_COLORS`: list of cycling border color names
- `QUIPS`: list of coffee-themed messages
- `PAUSED_QUIP`: fixed message for paused state
- `get_steam_frame(elapsed, paused)`: returns the current steam art (or blank if paused)
- `get_cup_art(paused)`: returns the coffee cup with appropriate fill style
- `get_border_color(elapsed, paused)`: returns the current border color
- `get_quip(elapsed, paused)`: returns the current quip string
- `build_animated_display(...)`: assembles the full panel content with cup + status side by side

### Modified: `src/digital_caffeine/cli.py`

- `build_display` is replaced/updated to call `build_animated_display` from the animations module
- The existing `Live` loop passes elapsed seconds which drives all animation state
- No additional threads or timers needed

### Animation state

Purely functional - driven by elapsed seconds:

- `steam_frame` = `elapsed % 4`
- `border_color` = cycles through 4 shades
- `quip_index` = `(elapsed // 8) % len(quips)`

### Files NOT changed

- `engine.py` - no changes
- `tray.py` - no changes (animations are CLI-only)
- `config.py` - no changes
- `constants.py` - no changes
