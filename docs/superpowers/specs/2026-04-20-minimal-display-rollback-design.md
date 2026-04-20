# Minimal Display Rollback - Design Spec

**Date:** 2026-04-20
**Status:** Approved
**Author:** Blake (with Claude)

## Motivation

The CLI display has drifted far from the project's actual purpose. Digital Caffeine is a one-syscall-in-a-loop utility that keeps Windows awake, but the display layer has grown into a PC-98 visual novel: a 1,225-line `pc98/` package with a Textual app, pixel canvas, 16-color palette cycling, sprites, particle systems, scene compositor, and status/dialogue widgets. On top of that, `animations.py` carries 834 lines of decorative chrome - coffee cup ASCII art, procedural steam, drip particles, typewriter quips, RGB rainbow borders, bubbling coffee, saucer glow.

The scope no longer fits the tool. This spec rolls the display back toward a minimal, Claude-Code-style surface: a single status line, breathing room, an occasional quip, and nothing else. "Highly adaptive" is the explicit goal - the display reflows to terminal width, degrades gracefully without color, and works in non-TTY contexts.

## Scope of the Cut

**Delete:**
- `src/digital_caffeine/pc98/` (all 10 files, ~1,225 lines)
- `tests/test_pc98_canvas.py`, `tests/test_pc98_palette.py`, `tests/test_pc98_particles.py`, `tests/test_pc98_scene.py`, `tests/test_pc98_sprites.py`, `tests/test_pc98_widgets.py` (~528 lines)
- `textual` from `pyproject.toml` dependencies

**Rewrite:**
- `src/digital_caffeine/animations.py` (834 lines → roughly 150-200 lines)
- `tests/test_animations.py` (293 lines → roughly 80-100 lines)

**Leave alone:**
- `src/digital_caffeine/engine.py`
- `src/digital_caffeine/config.py`
- `src/digital_caffeine/constants.py`
- `src/digital_caffeine/cli.py` (may need small tweaks if references to removed symbols exist)
- `src/digital_caffeine/tray.py`
- `src/digital_caffeine/icons.py`
- `pystray`, `Pillow`, `rich`, `click` dependencies
- `--simulate` (mouse jiggle) behavior - engine-level, unrelated to display
- Existing spec docs in `docs/superpowers/specs/` (historical record, not deleted)

## New `animations.py` Surface

The display is a single block redrawn in place via `rich.Live`, with three stacked zones:

```
 ⠋  caffeine · keeping display awake · 2h 13m 5s · q to quit

    a well-caffeinated mind is a dangerous thing
```

### Status line

`<spinner> caffeine · <mode phrase> · <elapsed>[· <remaining>] · q to quit`

- **Spinner:** one Braille spinner frame from Rich's built-in set (`dots`). Advances at the redraw FPS.
- **`<mode phrase>`:** derived from the current `Mode` enum value:
  - `Mode.DISPLAY` → `keeping display awake`
  - `Mode.SYSTEM` → `keeping system awake`
  - `Mode.ALL` → `keeping display + system awake`
- **Elapsed:** `Xh Ym Zs` with segments dropped as they hit zero on the left, no leading zeros (`5s`, `3m 2s`, `1h 0m 0s`, `2h 13m 5s`).
- **Duration suffix:** if `--duration` is set, append `· 1h 22m / 2h 30m left`. Uses the same "drop-left-zeros, no leading zeros" rule as elapsed, but seconds are always omitted for the duration suffix (duration input is minute-granular, showing seconds here adds noise).
- **Quit hint:** `· q to quit` when stdin is a TTY and the app is listening for keys. Omitted otherwise.
- **Paused state:** when the engine reports paused (tray mode can pause), mode phrase becomes `paused` and the spinner uses a single static frame (no rotation).
- **Color:** one dim accent (dim cyan direction) on the `caffeine` token and the remaining duration suffix. Everything else is default foreground. `NO_COLOR` env disables all accent.

### Blank line

One empty line between status and quip. Non-negotiable for the Claude-Code-style feel.

### Quip line

- One quip from the existing 120-quip pool.
- Rotates every ~90 seconds (module-level constant, not a flag).
- Dim styling.
- Empty string for the first ~5 seconds of the session so the first frame isn't noisy.

### Adaptive behavior

- Reflows to terminal width via Rich's built-in wrapping. No fixed column counts.
- Width < 50 cols: drop the `· q to quit` suffix and the `/ <total> left` fragment. Keep spinner, `caffeine`, mode phrase, elapsed.
- `sys.stdout.isatty()` is False (piped/redirected): skip `Live` entirely. Print a single line `caffeine: keeping display awake (press Ctrl+C to stop)` and let the engine run. No redraw loop.
- `FPS` constant: 2 (down from 8). Spinner still feels alive; elapsed only ticks at 1 Hz anyway.

### Public surface

The module exports exactly one function:

```python
def run_display(engine, mode, duration_seconds: int | None) -> None: ...
```

Blocking call. Returns when the engine stops or the user hits `q` / Ctrl+C. All other helpers (mode phrase lookup, elapsed formatter, quip picker) are module-private.

### What's explicitly gone

Coffee cup ASCII, procedural steam, drip particles, typewriter quips, RGB border cycle, bubbling coffee, saucer glow, breathing footer, per-character color gradients, palette cycling, half-block canvas, sprites. The entire `pc98/` package and its Textual integration.

## Testing Strategy

### Deleted tests

The six `tests/test_pc98_*.py` files (~528 lines) are removed outright.

### Rewritten tests

`tests/test_animations.py` is rebuilt against the new surface:

- `test_run_display_in_non_tty_mode` - monkeypatch `sys.stdout.isatty` to False; confirm the one-line fallback is printed and no `Live` context is opened.
- `test_status_line_reflow_narrow_terminal` - at terminal width 40, output omits `q to quit` and the duration-remaining fragment.
- `test_status_line_elapsed_formatting` - boundary cases for the elapsed formatter: 0s, 59s, 1m, 59m 59s, 1h 0m 0s, 2h 3m 5s.
- `test_mode_phrase_for_each_mode` - all three `Mode` values map to their expected phrase.
- `test_paused_mode_phrase` - when the engine reports paused, phrase is `paused` and the spinner uses the static frame.
- `test_no_color_env_disables_accent` - with `NO_COLOR=1`, no ANSI color codes appear in output.
- `test_quip_rotation_cadence` - freeze time, advance past the cadence threshold, confirm a different quip is selected.

No tests for the `rich.Live` redraw loop itself - that's library behavior and hard to assert against. The strategy is to test the pure functions (mode phrase, elapsed formatter, width-based suffix selection, quip picker) plus one smoke test for the non-TTY fallback.

### Untouched tests

`tests/test_cli.py`, `tests/test_engine.py`, `tests/test_config.py`. CLI tests may need a minor tweak if they reference a symbol that no longer exists, but no command-surface changes are in scope.

### Test LOC delta

Total drops from 1,456 to roughly 820 lines. Roughly halves, which tracks with the scope cut.

## Non-Goals

- **Not changing CLI commands.** `caffeine start`, `caffeine start --tray`, `caffeine start --duration 2h30m`, `caffeine start --simulate`, `caffeine config --*`, `caffeine version` all behave the same.
- **Not changing engine behavior.** `SetThreadExecutionState` calls, pause/resume semantics, duration expiry, `--simulate` mouse jiggle all unchanged.
- **Not changing tray mode.** `tray.py` and `icons.py` stay as-is.
- **Not cleaning up historical spec docs.** The two prior overhaul specs (`2026-04-03-animation-overhaul-design.md`, `2026-04-03-pc98-overhaul-design.md`) remain in place as historical record.
- **No new features.** This is pure simplification.

## Open Questions

None at spec-writing time. If the implementation surfaces a real ambiguity, it will be flagged back to Blake rather than resolved unilaterally.
