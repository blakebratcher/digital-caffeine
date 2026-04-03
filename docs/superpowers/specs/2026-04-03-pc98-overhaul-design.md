# PC-98 Visual Novel Display Overhaul - Design Spec

## Summary

Replace the current Rich `Panel` + `Live` loop display with a full PC-98 game screen experience. Visual novel layout rendered with Pillow-based pixel art using the half-block character technique. Textual `App` framework drives the UI with custom widgets. Authentic 16-color warm PC-98 palette, palette cycling animation tricks, scanline CRT effects, particle systems, and a VN-style dialogue box for quips.

## Goals

- Look and feel like a lovingly crafted PC-98 game utility screen
- Large 64x80 pixel art coffee scene (32x40 terminal cells) with detailed cup, steam, table, background
- Visual novel layout: art left, status panel right, dialogue box bottom
- Authentic 16-color warm palette with ordered dithering between shades
- Palette cycling tricks for liquid shimmer, steam glow, and border accents
- Scanline overlay for CRT authenticity
- Startup title card
- Graceful fallback to current Rich display for unsupported terminals

## Architecture Change

**Current:** `animations.py` builds Rich markup strings, `cli.py` drives a `Rich.Live` loop at 24 FPS rendering a single `Panel`.

**New:** A Textual `App` with custom widgets. A `PixelCanvas` widget wraps a Pillow `Image` framebuffer and renders it as half-block characters (each cell = 2 vertical pixels using fg+bg color on Unicode half-blocks). Separate widgets handle the status panel and dialogue box. The app's `set_interval` drives animation at 24 FPS.

### Half-Block Pixel Technique

Each terminal character cell represents 2 vertical pixels using:
- `\u2580` (upper half block) - fg = top pixel, bg = bottom pixel
- `\u2584` (lower half block) - fg = bottom pixel, bg = top pixel
- Full block or space for same-color pairs

A 64x80 pixel art image becomes 32x40 terminal cells. Rich `Text` or Textual `Strip` objects carry per-character `Style(color=fg, bgcolor=bg)` for truecolor output.

## Color Palette (16 colors)

Warm PC-98 palette inspired by Touhou, YU-NO, and Policenauts. All pixel art uses only these 16 indices. Gradients are achieved through ordered dithering, not color interpolation.

| Index | Name | Hex | Primary Use |
|-------|------|-----|-------------|
| 0 | Black | `#000000` | Outlines, background base |
| 1 | Deep Navy | `#1A0A2E` | Background fill, deep shadows |
| 2 | Dark Brown | `#3A1A06` | Deepest coffee layer |
| 3 | Warm Brown | `#8B4513` | Medium coffee |
| 4 | Chocolate | `#B8520A` | Light coffee |
| 5 | Amber | `#D2691E` | Crema, warm highlights |
| 6 | Gold | `#FFB347` | Shimmer accents, glow |
| 7 | Cream | `#FFDEAD` | Foam, light surfaces |
| 8 | Deep Red | `#8B0000` | Warm accent |
| 9 | Magenta | `#AA3377` | PC-98 signature tint |
| 10 | Dusty Rose | `#CC8899` | Soft highlights |
| 11 | Steel Blue | `#4477AA` | Cool contrast, UI borders |
| 12 | Slate | `#556677` | Metal, saucer |
| 13 | Warm Gray | `#887766` | Table, neutral surfaces |
| 14 | Light Gray | `#CCBBAA` | Cup body, rim |
| 15 | Off-White | `#EEDDCC` | Brightest highlights |

## Screen Layout

Minimum terminal size: 80 columns x 40 rows. The layout uses Textual's CSS grid or container system.

```
+==============================================================================+
|  Digital Caffeine                                             PC-98 ver.     |
+==========================================+===================================+
|                                          |  +---------------------------+    |
|   64x80 pixel art scene                 |  |  STATUS                   |    |
|   (32x40 half-block cells)              |  +---------------------------+    |
|                                          |  |  State:    * Active       |    |
|   Background: deep navy + dithering      |  |  Mode:     Display+Sys    |    |
|   Steam: particle wisps rising           |  |  Uptime:   00:12:34       |    |
|   Cup: detailed pixel art with           |  |  Remain:   Indefinite     |    |
|        gradient coffee fill              |  |  Interval: 60s            |    |
|   Table: wood-grain surface              |  |  Simulate: Off            |    |
|   Scanlines: every-other-row darken      |  +---------------------------+    |
|                                          |                                   |
|                                          |  +---------------------------+    |
|                                          |  |  ########~~~~~ 68%       |    |
|                                          |  +---------------------------+    |
+==========================================+===================================+
|  [ CAFFEINE ]                                                                |
|  Brewing productivity..._                                                    |
+==============================================================================+
```

### Title Bar
- Top border with "Digital Caffeine" left-aligned, "PC-98 ver." right-aligned
- Uses double-line box drawing characters
- Title text in gold (#FFB347), border in steel blue (#4477AA)

### Pixel Art Area (left, ~42 columns)
- `PixelCanvas` widget rendering a 64x80 Pillow `Image` as 32x40 half-block cells
- Scene includes: background, steam particles, coffee cup, table surface
- Scanline post-processing darkens every other pixel row by ~20%

### Status Panel (right, ~36 columns)
- Single-line box-drawn border in steel blue
- "STATUS" header in gold
- Fields rendered as PC-98 styled text (palette colors only)
- "Active" pulses between two green-ish palette shades
- Uptime flashes accent color on each second tick
- Progress bar uses dithered fill (palette index 11 filled, palette index 0 empty)

### Dialogue Box (bottom, full width, 4 rows)
- Double-line border in steel blue
- Speaker label `[ CAFFEINE ]` in gold, top-left of the box
- Quip text appears with typewriter effect (~8 chars/sec)
- Blinking block cursor during typing, disappears when complete
- Quip content reused from existing `_ALL_QUIPS` list

## Pixel Art Scene Details

### Background (64x80 full area)
- Fill with deep navy (#1A0A2E)
- Subtle 2x2 checkerboard dithering: alternate pixels between index 0 (black) and index 1 (deep navy) in a grid pattern
- Creates depth without using more colors

### Steam (upper ~30 rows of the scene)
- 6-8 particle wisps, each 2-3 pixels wide
- Each wisp has: x, y position, horizontal amplitude, frequency, age
- Movement: rise 0.5 pixels/frame, drift horizontally via sine wave
- Color by age: cream (#FFDEAD) near cup mouth, fading through warm gray (#887766) to near-invisible (deep navy blend) over ~40 frames
- Palette cycling trick: the 3-4 steam shades rotate their assignments every 4 frames, creating a shimmer effect without recomputing positions

### Coffee Cup (~rows 25-65, centered horizontally)

**Outline:** 1px black (#000000) border around all cup edges

**Rim:** 2px thick, off-white (#EEDDCC) with light gray (#CCBBAA) inner edge

**Body:** Light gray (#CCBBAA) walls, 2px thick on each side

**Coffee fill (inside the cup walls), top to bottom:**
1. Crema layer (2-3px): Cream (#FFDEAD) and amber (#D2691E) with 2x2 ordered dithering
2. Light coffee (4-5px): Chocolate (#B8520A) with occasional amber dither pixels
3. Medium coffee (5-6px): Warm brown (#8B4513) with chocolate dither
4. Dark coffee (5-6px): Dark brown (#3A1A06) with warm brown dither
5. Deepest (remaining): Solid dark brown (#3A1A06)

Each layer boundary uses checkerboard dithering between the two adjacent colors for smooth PC-98 style gradients.

**Coffee surface animation:** The top 2 rows of coffee (crema) use palette cycling. Indices 5/6/7 (amber/gold/cream) rotate every 4 frames, creating a ripple/shimmer effect on the liquid surface.

**Handle:** Right side of cup, warm gray (#887766) with 1px off-white highlight on top edge. Connected to cup body at ~30% and ~70% height.

**Saucer:** Below cup, slate (#556677) oval/rectangle shape with 1px light gray highlight on top edge. Wider than the cup by ~4px on each side.

### Table Surface (bottom ~20 rows)
- Warm gray (#887766) base fill
- Horizontal 1px lines in light gray (#CCBBAA) every 4 pixels for wood grain
- Subtle dithering between warm gray and warm brown (#8B4513) for texture

### Drip Particles
- Spawn below the cup bottom, within the saucer area or just off it
- 1-2 pixels, fall 1px/frame for 8-10 frames
- Color: chocolate (#B8520A) fading to warm brown (#8B4513)
- Max 2 active drips, spawn interval ~60 frames (~2.5 seconds)

## Animation Systems

### Palette Cycling
The signature PC-98 animation technique. Instead of redrawing pixels, rotate which color index maps to which RGB value.

- **Coffee surface:** Indices 5/6/7 cycle positions every 4 frames (3-step rotation = 12-frame cycle)
- **Steam glow:** Indices 7/13/1 cycle for steam particles every 6 frames
- **Border accent:** The UI border highlight color cycles through all 16 palette indices over ~8 seconds

Implementation: maintain a `palette_offset` counter. When rendering, the pixel art stores palette indices (0-15). The renderer maps index to RGB using `(index + offset) % cycle_length` for the cycling groups.

### Particle System
Two particle types sharing a common update loop:

**Steam particles:**
- Pool of 6-8 particles, always active
- Each frame: y -= 0.5, x += sin(frame * freq + phase) * amplitude
- When a particle exits the top of the scene, reset to bottom (near cup mouth) with new random-ish phase
- Render as 2-3 pixel wide marks at the particle's integer position

**Drip particles:**
- Pool of 2 particles, spawn on a timer
- Each frame: y += 1.0
- When a drip exceeds lifespan, mark inactive
- Spawn check every 60 frames, ~40% chance

### Scanline Effect
Post-processing pass on the Pillow framebuffer before half-block conversion:
- Every odd-numbered pixel row: darken RGB values by ~20% (multiply by 0.8)
- Creates the characteristic horizontal line pattern of CRT monitors
- Applied every frame after scene composition, before rendering to terminal

### Startup Title Card
On app mount, display a 1.5-second title screen:
- "DIGITAL CAFFEINE" in large pixel font (can be a simple blocky font drawn with Pillow)
- Centered on the full screen area
- Gold (#FFB347) text on deep navy (#1A0A2E) background
- Fade transition: over ~0.5 seconds, cross-fade to the main display by gradually revealing the main scene

### Status Animations
- "Active" text alternates between two shades every 30 frames
- Uptime display flashes gold for 2 frames on each second boundary
- Progress bar fill uses dithered pattern (alternating filled/half characters)

### Dialogue Box Animations
- Typewriter: 1 character every 3 frames (~8 chars/sec at 24 FPS)
- Block cursor (palette index 15) blinks on 18-frame cycle during typing
- Cursor disappears when quip is fully revealed
- 12-second total per quip (typing phase + hold)

## File Structure

```
src/digital_caffeine/
    __init__.py         # unchanged
    __main__.py         # unchanged
    engine.py           # unchanged
    cli.py              # MODIFIED - launch PC98App, fallback to old display
    config.py           # unchanged
    constants.py        # unchanged
    tray.py             # unchanged
    icons.py            # unchanged
    animations.py       # KEPT - quips list, format_time, quip logic reused
    pc98/               # NEW package
        __init__.py
        app.py          # PC98App(textual.App) - main application
        canvas.py       # PixelCanvas widget - Pillow framebuffer to half-block
        scene.py        # CoffeeScene - composites all pixel art layers
        sprites.py      # Draw functions: cup, steam, table, background
        palette.py      # 16-color palette, cycling logic, dithering helpers
        status.py       # StatusPanel widget
        dialogue.py     # DialogueBox widget
        title.py        # Startup title card screen
```

### Dependency Impact
- `textual>=0.80` added to `dependencies` in pyproject.toml (already installed)
- `Pillow` already a dependency
- No other new dependencies

### CLI Integration
In `cli.py`, the `start` command:
1. Check terminal capabilities: `Console().color_system == "truecolor"` and size >= 80x40
2. If supported: launch `PC98App` with engine parameters
3. If not: fall back to existing `Rich.Live` display (current `build_animated_display`)
4. `--tray` mode is unaffected

### Engine Integration
`PC98App` creates and manages `CaffeineEngine` the same way the current CLI loop does:
- `engine.start()` on app mount
- `engine.pause()` / `engine.resume()` on keypress
- `engine.stop()` on app exit / Ctrl+C
- Uptime, duration, mode, interval read from engine state each frame

## What Does NOT Change
- `CaffeineEngine` and all keep-awake logic
- System tray mode
- Config system
- CLI command structure and all flags
- Quip content
- Test structure for engine/config/CLI (display tests will need updates)

## Animation Rate Summary

| Element | Rate at 24 FPS | Cycle Length |
|---------|----------------|--------------|
| Scene render | Every frame | Continuous |
| Palette cycling (coffee) | Every 4 frames | 12-frame (0.5s) |
| Palette cycling (steam) | Every 6 frames | 18-frame (0.75s) |
| Border accent cycle | Every 4 frames | ~8s full rotation |
| Steam particle update | Every frame | ~40-frame lifespan |
| Drip particle spawn | Every 60 frames | 8-10 frame lifespan |
| Scanline overlay | Every frame | Static pattern |
| Title card | Once on startup | 1.5s duration |
| Typewriter | 1 char / 3 frames | 12s per quip |
| Cursor blink | 18-frame period | 0.75s |
| Status pulse | Every 30 frames | 1.25s |

## Test Impact
- Existing engine/config/CLI tests: unchanged
- Animation tests: update imports if functions move, but quip logic stays in `animations.py`
- New tests needed for: palette cycling logic, half-block renderer, particle system, scene composition
- Title card and visual rendering are hard to unit test - focus on data/logic layer tests

## Terminal Requirements
- Truecolor support (24-bit RGB)
- Minimum 80x40 terminal size
- Unicode support (half-block characters)
- Falls back to current Rich display if requirements not met
