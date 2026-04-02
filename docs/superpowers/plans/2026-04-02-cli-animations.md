# CLI Animations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add coffee-themed animations (steam, cup art, pulsing border, rotating quips) to the CLI live display.

**Architecture:** A new `animations.py` module owns all animation data and rendering. All animation state is purely functional - driven by an elapsed-seconds integer, no threads or timers. `cli.py` calls into `animations.py` instead of building plain text panels.

**Tech Stack:** Python 3.10+, Rich (already a dependency)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `src/digital_caffeine/animations.py` | Create | Steam frames, cup art, quips, border colors, `build_animated_display()` |
| `src/digital_caffeine/cli.py` | Modify | Replace `build_display` with call to `build_animated_display` |
| `tests/test_animations.py` | Create | Unit tests for all animation functions |

---

### Task 1: Animation Data and Helper Functions

**Files:**
- Create: `tests/test_animations.py`
- Create: `src/digital_caffeine/animations.py`

- [ ] **Step 1: Write failing tests for animation helpers**

Create `tests/test_animations.py`:

```python
"""Tests for the Digital Caffeine CLI animations module."""

from __future__ import annotations

from digital_caffeine.animations import (
    BORDER_COLORS,
    PAUSED_QUIP,
    QUIPS,
    STEAM_FRAMES,
    get_border_color,
    get_cup_art,
    get_quip,
    get_steam_frame,
)


# -- Steam frame tests --


def test_steam_frames_has_four_frames() -> None:
    assert len(STEAM_FRAMES) == 4


def test_get_steam_frame_cycles_through_frames() -> None:
    for i in range(4):
        result = get_steam_frame(elapsed=i, paused=False)
        assert result == STEAM_FRAMES[i]


def test_get_steam_frame_wraps_around() -> None:
    assert get_steam_frame(elapsed=4, paused=False) == STEAM_FRAMES[0]
    assert get_steam_frame(elapsed=7, paused=False) == STEAM_FRAMES[3]


def test_get_steam_frame_paused_returns_blank_lines() -> None:
    result = get_steam_frame(elapsed=0, paused=True)
    # Should be blank lines (no steam), same number of lines as a normal frame
    lines = result.split("\n")
    assert all(line.strip() == "" for line in lines)


# -- Cup art tests --


def test_get_cup_art_active_has_bold_fill() -> None:
    result = get_cup_art(paused=False)
    assert "\u2593" in result  # dark shade character


def test_get_cup_art_paused_has_dim_fill() -> None:
    result = get_cup_art(paused=True)
    assert "\u2591" in result  # light shade character


# -- Border color tests --


def test_border_colors_has_four_entries() -> None:
    assert len(BORDER_COLORS) == 4


def test_get_border_color_cycles() -> None:
    colors = [get_border_color(elapsed=i, paused=False) for i in range(8)]
    assert colors == BORDER_COLORS + BORDER_COLORS


def test_get_border_color_paused_returns_yellow() -> None:
    assert get_border_color(elapsed=0, paused=True) == "yellow"
    assert get_border_color(elapsed=3, paused=True) == "yellow"


# -- Quip tests --


def test_quips_has_at_least_ten() -> None:
    assert len(QUIPS) >= 10


def test_get_quip_rotates_every_eight_seconds() -> None:
    quip_0 = get_quip(elapsed=0, paused=False)
    quip_same = get_quip(elapsed=7, paused=False)
    quip_next = get_quip(elapsed=8, paused=False)
    assert quip_0 == quip_same  # same within 8s window
    assert quip_0 != quip_next  # different after 8s


def test_get_quip_wraps_around() -> None:
    cycle_length = len(QUIPS) * 8
    assert get_quip(elapsed=0, paused=False) == get_quip(elapsed=cycle_length, paused=False)


def test_get_quip_paused_returns_paused_quip() -> None:
    assert get_quip(elapsed=0, paused=True) == PAUSED_QUIP
    assert get_quip(elapsed=99, paused=True) == PAUSED_QUIP
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_animations.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'digital_caffeine.animations'`

- [ ] **Step 3: Implement animation data and helpers**

Create `src/digital_caffeine/animations.py`:

```python
"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

# -- Steam frames (4 frames, each 2 lines tall) ------------------------------
# Characters cycle upward to create a rising-steam illusion.

STEAM_FRAMES: list[str] = [
    "    ~ ~  \n   ( _ ) ",
    "   ( _ ) \n    ~ ~  ",
    "   ~ . ~ \n  (  ~  )",
    "  (  ~  )\n   ~ . ~ ",
]

_BLANK_STEAM: str = "         \n         "


def get_steam_frame(elapsed: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A two-line string of steam art, or blank lines if paused.
    """
    if paused:
        return _BLANK_STEAM
    return STEAM_FRAMES[elapsed % len(STEAM_FRAMES)]


# -- Cup art ------------------------------------------------------------------

_CUP_ACTIVE: str = (
    "   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510 \u2510\n"
    "   \u2502\u2593\u2593\u2593\u2593\u2593\u2593\u2593\u2502 \u2502\n"
    "   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518 \u2518"
)

_CUP_PAUSED: str = (
    "   \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510 \u2510\n"
    "   \u2502\u2591\u2591\u2591\u2591\u2591\u2591\u2591\u2502 \u2502\n"
    "   \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518 \u2518"
)


def get_cup_art(*, paused: bool) -> str:
    """Return the coffee cup ASCII art.

    Args:
        paused: Whether the engine is paused (shows dim fill).

    Returns:
        A three-line string of cup art.
    """
    return _CUP_PAUSED if paused else _CUP_ACTIVE


# -- Border colors (4-step breathing cycle) -----------------------------------

BORDER_COLORS: list[str] = ["cyan", "dark_cyan", "bright_cyan", "dark_cyan"]


def get_border_color(elapsed: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A Rich color name string.
    """
    if paused:
        return "yellow"
    return BORDER_COLORS[elapsed % len(BORDER_COLORS)]


# -- Quips --------------------------------------------------------------------

QUIPS: list[str] = [
    "Brewing productivity...",
    "Your PC is caffeinated",
    "Sleep is for the weak (and not this PC)",
    "Keeping things percolating...",
    "Another cup? Don't mind if I do",
    "Drip, drip, drip... staying awake",
    "Freshly brewed and wide awake",
    "No decaf allowed here",
    "Espresso yourself freely",
    "A latte work getting done today",
    "Grounds for staying awake",
    "This machine runs on caffeine",
]

PAUSED_QUIP: str = "Gone cold... resume to reheat"


def get_quip(elapsed: int, *, paused: bool) -> str:
    """Return the current quip message.

    Args:
        elapsed: Seconds since the engine started.
        paused: Whether the engine is paused.

    Returns:
        A quip string.
    """
    if paused:
        return PAUSED_QUIP
    return QUIPS[(elapsed // 8) % len(QUIPS)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -v`
Expected: All 13 tests PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/digital_caffeine/animations.py tests/test_animations.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: add animation data and helper functions for CLI display"
```

---

### Task 2: build_animated_display Function

**Files:**
- Modify: `src/digital_caffeine/animations.py` (append to end)
- Modify: `tests/test_animations.py` (append new tests)

- [ ] **Step 1: Write failing tests for build_animated_display**

Append to `tests/test_animations.py`:

```python
from rich.panel import Panel

from digital_caffeine.animations import build_animated_display
from digital_caffeine.constants import Mode


def test_build_animated_display_returns_panel() -> None:
    result = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert isinstance(result, Panel)


def test_build_animated_display_contains_status_info() -> None:
    from rich.console import Console
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    panel = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=65,
        duration_seconds=3600,
        interval=60,
        paused=False,
        simulate=True,
    )
    console.print(panel)
    output = buf.getvalue()

    assert "Active" in output
    assert "Display + System" in output
    assert "00:01:05" in output  # uptime
    assert "00:58:55" in output  # remaining
    assert "60s" in output


def test_build_animated_display_paused_state() -> None:
    from rich.console import Console
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    panel = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=10,
        duration_seconds=None,
        interval=60,
        paused=True,
        simulate=False,
    )
    console.print(panel)
    output = buf.getvalue()

    assert "Paused" in output
    assert "Gone cold" in output


def test_build_animated_display_border_color_changes() -> None:
    panel_0 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    panel_1 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=1,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    # Border styles should differ between frame 0 and frame 1
    assert panel_0.border_style != panel_1.border_style


def test_build_animated_display_quip_rotates() -> None:
    from rich.console import Console
    from io import StringIO

    buf_0 = StringIO()
    console_0 = Console(file=buf_0, force_terminal=True, width=80)
    panel_0 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_0.print(panel_0)

    buf_8 = StringIO()
    console_8 = Console(file=buf_8, force_terminal=True, width=80)
    panel_8 = build_animated_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=8,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_8.print(panel_8)

    # The quip text should differ between second 0 and second 8
    assert buf_0.getvalue() != buf_8.getvalue()
```

- [ ] **Step 2: Run tests to verify the new tests fail**

Run: `pytest tests/test_animations.py::test_build_animated_display_returns_panel -v`
Expected: FAIL with `ImportError: cannot import name 'build_animated_display'`

- [ ] **Step 3: Implement build_animated_display**

Append to the end of `src/digital_caffeine/animations.py`:

```python
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from digital_caffeine.constants import Mode

# Maps Mode enum to display labels (same as cli.py uses)
_MODE_DISPLAY: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def _format_time(seconds: int) -> str:
    """Format an integer number of seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_animated_display(
    *,
    mode: Mode,
    uptime_seconds: int,
    duration_seconds: int | None,
    interval: int,
    paused: bool,
    simulate: bool,
) -> Panel:
    """Build an animated Rich Panel showing keep-awake status with coffee art.

    Args:
        mode: Active prevention mode.
        uptime_seconds: How long the engine has been running.
        duration_seconds: Total requested duration (None if indefinite).
        interval: Refresh interval in seconds.
        paused: Whether the engine is currently paused.
        simulate: Whether input simulation is enabled.

    Returns:
        A Rich Panel with animated coffee cup, status info, and a quip.
    """
    steam = get_steam_frame(uptime_seconds, paused=paused)
    cup = get_cup_art(paused=paused)
    border_color = get_border_color(uptime_seconds, paused=paused)
    quip = get_quip(uptime_seconds, paused=paused)

    # Status values
    status_str = "[yellow]Paused[/yellow]" if paused else "[green]Active[/green]"

    if duration_seconds is not None:
        remaining = max(0, duration_seconds - uptime_seconds)
        remaining_str = _format_time(remaining)
    else:
        remaining_str = "Indefinite"

    sim_str = "[green]On[/green]" if simulate else "[dim]Off[/dim]"

    # Build the two-column layout as aligned text lines.
    # Left column: steam (2 lines) + cup (3 lines) = 5 art lines
    # Right column: status fields aligned beside the art
    steam_lines = steam.split("\n")
    cup_lines = cup.split("\n")
    art_lines = steam_lines + cup_lines

    status_fields = [
        f"Status:         {status_str}",
        f"Mode:           {_MODE_DISPLAY.get(mode, str(mode))}",
        f"Uptime:         {_format_time(uptime_seconds)}",
        f"Time remaining: {remaining_str}",
        f"Interval:       {interval}s",
    ]

    # Pad art lines to a uniform width for alignment
    art_width = 20
    combined_lines: list[str] = []
    max_rows = max(len(art_lines), len(status_fields))
    for i in range(max_rows):
        left = art_lines[i] if i < len(art_lines) else ""
        right = status_fields[i] if i < len(status_fields) else ""
        combined_lines.append(f"  {left:<{art_width}} {right}")

    # Simulate line (below the main grid)
    combined_lines.append(f"  {'':>{art_width}} Simulate:       {sim_str}")

    # Quip line
    combined_lines.append("")
    if paused:
        combined_lines.append(f"  [yellow dim italic]{quip}[/yellow dim italic]")
    else:
        combined_lines.append(f"  [dim italic]{quip}[/dim italic]")

    # Ctrl+C hint
    combined_lines.append("")
    combined_lines.append("  [dim]Press Ctrl+C to stop[/dim]")

    content = "\n".join(combined_lines)
    return Panel(
        content,
        title="[bold cyan]:coffee: Digital Caffeine[/bold cyan]",
        border_style=Style(color=border_color),
        padding=(1, 2),
    )
```

- [ ] **Step 4: Run all animation tests to verify they pass**

Run: `pytest tests/test_animations.py -v`
Expected: All 18 tests PASS

- [ ] **Step 5: Lint**

Run: `ruff check src/digital_caffeine/animations.py tests/test_animations.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: add build_animated_display for coffee-themed CLI panel"
```

---

### Task 3: Integrate into CLI

**Files:**
- Modify: `src/digital_caffeine/cli.py:1-13` (imports), `src/digital_caffeine/cli.py:83-130` (build_display), `src/digital_caffeine/cli.py:236-266` (Live loop)
- Modify: `tests/test_cli.py` (update import if needed)

- [ ] **Step 1: Write a test verifying CLI uses animated display**

Append to `tests/test_cli.py`:

```python
from digital_caffeine.cli import build_display
from digital_caffeine.constants import Mode
from rich.panel import Panel


def test_build_display_returns_animated_panel() -> None:
    """build_display should delegate to the animated display builder."""
    panel = build_display(
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert isinstance(panel, Panel)

    # Verify it has animated content by checking for coffee cup character
    from rich.console import Console
    from io import StringIO

    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=80)
    console.print(panel)
    output = buf.getvalue()
    # The cup should contain box-drawing characters from the animated display
    assert "\u2502" in output  # vertical box line from cup art
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_cli.py::test_build_display_returns_animated_panel -v`
Expected: FAIL - the current `build_display` does not include cup art characters in the expected layout

- [ ] **Step 3: Update build_display in cli.py to delegate to animations**

Replace the `build_display` function body in `src/digital_caffeine/cli.py`. Change the import block to add `build_animated_display`, then replace `build_display` so it delegates:

At the top of `cli.py`, add this import:

```python
from digital_caffeine.animations import build_animated_display
```

Replace the `build_display` function (lines 83-130) with:

```python
def build_display(
    *,
    mode: Mode,
    uptime_seconds: int,
    duration_seconds: int | None,
    interval: int,
    paused: bool,
    simulate: bool,
) -> Panel:
    """Build a Rich Panel showing the current keep-awake status with animations.

    Delegates to the animations module for coffee-themed display.
    """
    return build_animated_display(
        mode=mode,
        uptime_seconds=uptime_seconds,
        duration_seconds=duration_seconds,
        interval=interval,
        paused=paused,
        simulate=simulate,
    )
```

Remove the now-unused `MODE_DISPLAY` dict from `cli.py` (lines 28-32), since `build_animated_display` carries its own copy. The `MODE_DISPLAY` dict is still used in the `start` command's print statement (line 233) and the session summary (line 276), so replace those two references with inline `MODE_MAP` lookups. Specifically:

In the `start` function, change:

```python
console.print(
    f"[green]Digital Caffeine started[/green] - mode={MODE_DISPLAY[mode]}, interval={interval}s"
)
```

to:

```python
from digital_caffeine.animations import _MODE_DISPLAY as ANIM_MODE_DISPLAY
```

Actually, simpler: keep `MODE_DISPLAY` in `cli.py`. It's used in the startup message and session summary, which are outside the panel. No need to remove it. Just add the import and replace `build_display`'s body.

- [ ] **Step 4: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS (test_cli + test_animations + test_engine + test_config)

- [ ] **Step 5: Lint**

Run: `ruff check src/digital_caffeine/cli.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/digital_caffeine/cli.py tests/test_cli.py
git commit -m "feat: integrate animated coffee display into CLI"
```

---

### Task 4: Manual Smoke Test and Final Polish

**Files:**
- Possibly tweak: `src/digital_caffeine/animations.py` (art alignment)

- [ ] **Step 1: Run the CLI and visually verify animations**

Run: `caffeine start --simulate -d 30s`

Verify:
- Coffee cup renders with box-drawing characters
- Steam animates above the cup each second (4 distinct frames cycling)
- Border color pulses through cyan shades
- Quip text appears at the bottom in dim italic
- Quip rotates after ~8 seconds
- Status fields (uptime, remaining, mode, interval, simulate) display correctly
- Uptime counts up, remaining counts down

- [ ] **Step 2: Test paused state visually (if possible)**

If the CLI doesn't expose pause yet, skip this step. Otherwise verify:
- Steam disappears
- Cup fill dims
- Border turns yellow
- Quip shows "Gone cold... resume to reheat"

- [ ] **Step 3: Fix any alignment or rendering issues**

Adjust padding, art_width, or steam frame strings if the layout looks off in the terminal. No specific code here - depends on visual inspection.

- [ ] **Step 4: Run full test suite one final time**

Run: `pytest tests/ -v && ruff check src/ tests/`
Expected: All tests PASS, no lint errors

- [ ] **Step 5: Commit any polish tweaks**

```bash
git add -u
git commit -m "fix: polish animation layout after visual testing"
```

(Skip this commit if no changes were needed.)
