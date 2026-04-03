# Animation Overhaul - Design Spec

## Summary

Upgrade the CLI animation system from 8 FPS to 24 FPS with richer visual effects: full-spectrum rainbow border, heat-shimmer steam, coffee surface glow, drip particles, and handle breathing. All animation rates are decoupled from framerate so effects feel intentional at any FPS.

## Target File

`src/digital_caffeine/animations.py` - all changes are confined here. No changes to engine, CLI, tray, or tests structure needed (though test constants like `STEAM_FRAMES` length will need updating).

## Changes

### 1. Framerate

- `FPS = 24`
- All animation timing uses frame-count math relative to `FPS` so nothing accidentally speeds up 3x

### 2. Steam System

**Current:** 10 wisps, 5 rows tall, 24 pre-generated frames, gray palette

**New:**
- 14-16 wisps with varied amplitudes and frequencies
- 7 rows of steam headroom (`_STEAM_HEIGHT = 7`)
- 48 pre-generated frames (2 seconds of unique steam at 24 FPS)
- Wisps start warm near the cup (#AA8866, #997755) and cool to gray (#666666, #444444) as they rise
- Heat shimmer: occasional `*` characters near the bottom 1-2 rows in warm orange/yellow (#FFB347, #FFA500) that appear for 2-4 frames then vanish
- Steam half-speed: advance steam frame index at `frame // 3` instead of `frame // 2` to maintain natural rising speed at higher FPS
- Brightest wisps (bottom row) tint toward the current border hue - requires passing `frame` context through to color selection

### 3. Liquid Surface

**Current:** 8 surface patterns, single brown tone

**New:**
- 16 surface ripple patterns for less repetition
- Surface color oscillates between warm tones: #D2691E (chocolate) through #FFB347 (warm gold) and back, using sine interpolation over ~4 seconds
- Shimmer highlights: 1-2 random positions per frame get a bright `*` or `'` character in #FFD700 (gold) for 1-2 frames, simulating light catching the liquid

### 4. Cup Handle Breathing

- Handle characters (`|` sections of the handle) cycle between white and dim white (#AAAAAA) in sync with the border breathing cycle
- Reuse the border cycle phase, just map to a narrower brightness range

### 5. Coffee Drip Particles

- Small particle system: occasional `'` or `.` characters that spawn at the top cup line (row 0 of cup art, columns within the cup walls) and fall 1-2 rows over 6-10 frames
- Spawn rate: ~1 drip every 2-3 seconds (random)
- Color: warm brown matching the coffee fill (#B8520A fading to #8B4513)
- Max 2 active drips at once to keep it subtle
- Drips occupy the column space just below the cup art, integrated into existing line rendering

### 6. Rainbow Border

**Current:** 32-step cyan breathing cycle

**New:**
- 72-step full HSV hue rotation at constant saturation and brightness
- Cycle speed: full rotation in ~6 seconds (72 steps, advance every 2 frames = 36 effective steps/sec... 72/12 = 6s)
- Colors generated via HSV-to-RGB conversion: H cycles 0-360, S=0.7, V=0.85 for rich but not neon colors
- Paused state remains yellow (unchanged)

### 7. Quip Timing

**Current:** 2 chars per frame, 8 seconds per quip

**New:**
- 1 character every 3 frames = ~8 chars/second at 24 FPS - deliberate keystroke feel
- Quip display interval: 12 seconds total (typing phase + ~6 second hold)
- Blinking cursor unchanged (adjust blink rate to `frame % 18 < 9` for ~0.75 second blink period at 24 FPS)
- Self-referential quip "This animation runs at 8fps" updated to reflect 24 FPS

### 8. Steam Width

- `_STEAM_WIDTH` stays at 25 (sufficient for the wider wisp field)
- `art_width` in display assembly may need a bump from 26 to 28 if the taller steam adds visual width

## What Does NOT Change

- Cup shape and size (7 rows: top, 4 body, bottom, saucer)
- Cup art structure (white outline, gradient fills)
- Paused state behavior (no steam, dim cup, yellow border)
- Status field layout and content
- Progress bar
- Panel structure and Rich Panel API usage
- Quip content (except the one FPS self-reference)
- `get_steam_frame`, `get_cup_art`, `get_border_color`, `get_quip` function signatures

## Animation Rate Summary

| Element | Rate at 24 FPS | Cycle Length |
|---------|----------------|--------------|
| Border color | Every 2 frames | ~6s full rainbow |
| Steam advance | Every 3 frames | 48 unique frames = 6s |
| Surface ripple | Every 3 frames | 16 patterns = 2s |
| Surface glow | Continuous sine | ~4s warm oscillation |
| Shimmer highlights | Random per frame | Sporadic |
| Drip particles | ~1 spawn / 2-3s | 6-10 frame lifespan |
| Handle breathing | Every frame | Synced with border |
| Quip typewriter | 1 char / 3 frames | ~12s per quip |
| Cursor blink | 18-frame period | ~0.75s |

## Test Impact

- `test_steam_frames_are_generated`: Update assertion from 24 to 48 frames
- `FPS` constant assertions: Update from 8 to 24
- `BORDER_COLORS` length: Update from 32 to 72
- All behavioral tests (quip cycling, steam paused, etc.) should still pass with updated constants
