# Minimal Display Rollback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roll the CLI display back from the PC-98 visual novel and ornate `animations.py` to a Claude-Code-style minimal status line that reflows to terminal width, degrades on non-TTY, and honors `NO_COLOR`.

**Architecture:** New `animations.py` exports one public entry point, `run_display(engine, mode, duration_seconds)`, plus a tiny `format_elapsed` helper for the CLI session summary. Internals are pure functions tested in isolation (mode phrase, elapsed/duration formatters, quip picker, status-text builder). A `rich.Live` loop drives redraw on TTY; non-TTY prints one line and waits on the engine. The PC-98 package, its tests, and the `textual` dependency are deleted.

**Tech Stack:** Python 3.10+, Rich (Live, Console, Text), Click (CLI, unchanged), pytest + pytest-mock (testing). msvcrt (stdlib, Windows-only) for the `q`-to-quit key listener.

**Spec clarification:** The design spec leaves `format_elapsed` as "module-private." This plan promotes it to public (no leading underscore) because the CLI session summary needs it. All other helpers (`_format_duration`, `_mode_phrase`, `_pick_quip`, `_build_status_text`) stay private.

---

## Task 1: `format_elapsed` helper (TDD)

**Files:**
- Create: `src/digital_caffeine/animations.py` (replaces old 834-line file; wipe and start over)
- Create: `tests/test_animations.py` (replaces old 293-line file; wipe and start over)

- [ ] **Step 1: Wipe the old `animations.py` and replace with a stub**

Delete the entire contents of `src/digital_caffeine/animations.py` and replace with:

```python
"""Minimal status-line display for the Digital Caffeine CLI.

Public surface:
    run_display(engine, mode, duration_seconds) -> None
    format_elapsed(seconds) -> str
"""

from __future__ import annotations

FPS = 2
```

- [ ] **Step 2: Wipe the old `test_animations.py` and write the failing test**

Delete the entire contents of `tests/test_animations.py` and replace with:

```python
"""Tests for the minimal Digital Caffeine display."""

from __future__ import annotations

import pytest

from digital_caffeine.animations import format_elapsed


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0s"),
        (5, "5s"),
        (59, "59s"),
        (60, "1m 0s"),
        (61, "1m 1s"),
        (3599, "59m 59s"),
        (3600, "1h 0m 0s"),
        (3661, "1h 1m 1s"),
        (7385, "2h 3m 5s"),
    ],
)
def test_format_elapsed_boundary_cases(seconds: int, expected: str) -> None:
    assert format_elapsed(seconds) == expected


def test_format_elapsed_negative_clamps_to_zero() -> None:
    assert format_elapsed(-10) == "0s"
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `pytest tests/test_animations.py -v`
Expected: `ImportError: cannot import name 'format_elapsed' from 'digital_caffeine.animations'` (tests fail to collect).

- [ ] **Step 4: Implement `format_elapsed`**

Append to `src/digital_caffeine/animations.py`:

```python
def format_elapsed(seconds: int) -> str:
    """Format seconds as 'Xh Ym Zs' with leading zero segments dropped."""
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: all 10 parametrized cases plus the negative test pass.

- [ ] **Step 6: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): rewrite as minimal module, add format_elapsed"
```

---

## Task 2: `_format_duration` helper (TDD)

**Files:**
- Modify: `src/digital_caffeine/animations.py`
- Modify: `tests/test_animations.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_animations.py`:

```python
from digital_caffeine.animations import _format_duration


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0m"),
        (60, "1m"),
        (1800, "30m"),
        (3600, "1h 0m"),
        (5400, "1h 30m"),
        (7200, "2h 0m"),
        (9000, "2h 30m"),
    ],
)
def test_format_duration_omits_seconds(seconds: int, expected: str) -> None:
    assert _format_duration(seconds) == expected
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_animations.py::test_format_duration_omits_seconds -v`
Expected: `ImportError: cannot import name '_format_duration'`.

- [ ] **Step 3: Implement `_format_duration`**

Append to `src/digital_caffeine/animations.py`:

```python
def _format_duration(seconds: int) -> str:
    """Format seconds as 'Xh Ym' (no seconds). Clamps negatives to zero."""
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): add _format_duration for duration suffix"
```

---

## Task 3: `_mode_phrase` helper (TDD)

**Files:**
- Modify: `src/digital_caffeine/animations.py`
- Modify: `tests/test_animations.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_animations.py`:

```python
from digital_caffeine.animations import _mode_phrase
from digital_caffeine.constants import Mode


def test_mode_phrase_display_only() -> None:
    assert _mode_phrase(Mode.DISPLAY_ONLY, paused=False) == "keeping display awake"


def test_mode_phrase_system_only() -> None:
    assert _mode_phrase(Mode.SYSTEM_ONLY, paused=False) == "keeping system awake"


def test_mode_phrase_display_and_system() -> None:
    assert (
        _mode_phrase(Mode.DISPLAY_AND_SYSTEM, paused=False)
        == "keeping display + system awake"
    )


def test_mode_phrase_paused_overrides_mode() -> None:
    assert _mode_phrase(Mode.DISPLAY_AND_SYSTEM, paused=True) == "paused"
    assert _mode_phrase(Mode.DISPLAY_ONLY, paused=True) == "paused"
    assert _mode_phrase(Mode.SYSTEM_ONLY, paused=True) == "paused"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_animations.py -k mode_phrase -v`
Expected: ImportError for `_mode_phrase`.

- [ ] **Step 3: Implement `_mode_phrase`**

Append to `src/digital_caffeine/animations.py`:

```python
from digital_caffeine.constants import Mode

_MODE_PHRASES: dict[Mode, str] = {
    Mode.DISPLAY_ONLY: "keeping display awake",
    Mode.SYSTEM_ONLY: "keeping system awake",
    Mode.DISPLAY_AND_SYSTEM: "keeping display + system awake",
}

_PAUSED_PHRASE = "paused"


def _mode_phrase(mode: Mode, paused: bool) -> str:
    """Return the descriptive phrase for the current engine state."""
    if paused:
        return _PAUSED_PHRASE
    return _MODE_PHRASES[mode]
```

Move the `Mode` import to the top of the file with the other imports.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): add _mode_phrase with paused override"
```

---

## Task 4: Quip pool and `_pick_quip` (TDD)

**Files:**
- Modify: `src/digital_caffeine/animations.py`
- Modify: `tests/test_animations.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_animations.py`:

```python
from digital_caffeine.animations import QUIPS, _pick_quip


def test_quips_pool_has_at_least_one_hundred() -> None:
    assert len(QUIPS) >= 100


def test_pick_quip_is_empty_during_startup_window() -> None:
    for elapsed in range(5):
        assert _pick_quip(elapsed_seconds=elapsed, seed=42) == ""


def test_pick_quip_returns_a_pool_member_after_startup() -> None:
    quip = _pick_quip(elapsed_seconds=5, seed=42)
    assert quip in QUIPS


def test_pick_quip_changes_after_rotation_interval() -> None:
    # Rotation is 90 seconds. Two elapsed values that straddle the boundary
    # should (with overwhelming probability) yield different quips. Using
    # a fixed seed makes this deterministic.
    a = _pick_quip(elapsed_seconds=5, seed=42)
    b = _pick_quip(elapsed_seconds=5 + 90, seed=42)
    assert a != b


def test_pick_quip_same_within_rotation_window() -> None:
    a = _pick_quip(elapsed_seconds=5, seed=42)
    b = _pick_quip(elapsed_seconds=5 + 89, seed=42)
    assert a == b
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_animations.py -k quip -v`
Expected: ImportError for `QUIPS` / `_pick_quip`.

- [ ] **Step 3: Implement `QUIPS` and `_pick_quip`**

Append to `src/digital_caffeine/animations.py`:

```python
import os
import random

_QUIP_ROTATION_SECONDS = 90
_STARTUP_QUIET_SECONDS = 5

QUIPS: list[str] = [
    # --- PASTE THE FULL 120-ENTRY LIST FROM THE PRE-ROLLBACK animations.py ---
    # Copy the entries of the `_ALL_QUIPS` variable verbatim from the file
    # history (commit 889e6e0 or earlier, lines roughly 497-624 of the old
    # animations.py). Keep the comment dividers (-- coffee puns --, etc.)
    # for readability.
]


def _pick_quip(elapsed_seconds: int, seed: int | None = None) -> str:
    """Return the quip for this elapsed time, or empty during startup.

    The pool is shuffled with `seed` (defaults to the current process id so
    each session feels different). The active quip changes every
    _QUIP_ROTATION_SECONDS.
    """
    if elapsed_seconds < _STARTUP_QUIET_SECONDS:
        return ""
    rng = random.Random(seed if seed is not None else os.getpid())
    shuffled = rng.sample(QUIPS, len(QUIPS))
    idx = ((elapsed_seconds - _STARTUP_QUIET_SECONDS) // _QUIP_ROTATION_SECONDS) % len(
        shuffled
    )
    return shuffled[idx]
```

Move `import os` and `import random` to the top of the file with the other imports.

**Note:** The 120 quips are data, not logic. Open the pre-rollback `animations.py` in git (`git show 889e6e0:src/digital_caffeine/animations.py`) and copy the `_ALL_QUIPS` list contents into `QUIPS` verbatim. Do not edit or recurate them in this task.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: all tests pass. If `test_pick_quip_changes_after_rotation_interval` flakes, the seed or rotation index math is wrong.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): import 120-quip pool and add _pick_quip"
```

---

## Task 5: `_build_status_text` (TDD)

**Files:**
- Modify: `src/digital_caffeine/animations.py`
- Modify: `tests/test_animations.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/test_animations.py`:

```python
from io import StringIO

from rich.console import Console

from digital_caffeine.animations import _build_status_text


def _render(text, width: int = 100) -> str:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=width, no_color=False)
    console.print(text)
    return buf.getvalue()


def test_build_status_text_includes_mode_phrase_and_elapsed() -> None:
    text = _build_status_text(
        spinner_frame="\u280B",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=65,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text)
    assert "caffeine" in rendered
    assert "keeping display awake" in rendered
    assert "1m 5s" in rendered


def test_build_status_text_duration_suffix_when_duration_set() -> None:
    text = _build_status_text(
        spinner_frame="\u280B",
        mode=Mode.DISPLAY_AND_SYSTEM,
        elapsed_seconds=60 * 38,
        duration_seconds=60 * 120,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text)
    assert "1h 22m / 2h 0m left" in rendered


def test_build_status_text_quit_hint_when_requested() -> None:
    text = _build_status_text(
        spinner_frame="\u280B",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    assert "q to quit" in _render(text)


def test_build_status_text_narrow_terminal_drops_suffixes() -> None:
    text = _build_status_text(
        spinner_frame="\u280B",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=3600,
        paused=False,
        width=40,
        show_quit_hint=True,
        use_color=True,
    )
    rendered = _render(text, width=40)
    assert "q to quit" not in rendered
    assert "left" not in rendered
    # But mode phrase and elapsed are still there
    assert "keeping display awake" in rendered
    assert "30s" in rendered


def test_build_status_text_no_color_omits_ansi_codes() -> None:
    text = _build_status_text(
        spinner_frame="\u280B",
        mode=Mode.DISPLAY_ONLY,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=False,
        width=100,
        show_quit_hint=True,
        use_color=False,
    )
    # With use_color=False the Text has no styles attached; we check by
    # inspecting the style assignments directly rather than the rendered ANSI.
    for segment in text.render(Console()):
        assert segment.style is None or segment.style.color is None


def test_build_status_text_paused_uses_paused_phrase() -> None:
    text = _build_status_text(
        spinner_frame="\u2022",  # static frame for paused state
        mode=Mode.DISPLAY_AND_SYSTEM,
        elapsed_seconds=30,
        duration_seconds=None,
        paused=True,
        width=100,
        show_quit_hint=True,
        use_color=True,
    )
    assert "paused" in _render(text)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_animations.py -k build_status_text -v`
Expected: ImportError for `_build_status_text`.

- [ ] **Step 3: Implement `_build_status_text`**

Append to `src/digital_caffeine/animations.py`:

```python
from rich.text import Text

_NARROW_TERMINAL_COLS = 50
_ACCENT_STYLE = "cyan"
_DIM_STYLE = "dim"


def _build_status_text(
    *,
    spinner_frame: str,
    mode: Mode,
    elapsed_seconds: int,
    duration_seconds: int | None,
    paused: bool,
    width: int,
    show_quit_hint: bool,
    use_color: bool,
) -> Text:
    """Build the single-line status Text for a given snapshot of state.

    When `width` is below the narrow threshold, drops the quit hint and the
    duration-remaining suffix. When `use_color` is False, no styles are applied
    (NO_COLOR env).
    """
    narrow = width < _NARROW_TERMINAL_COLS
    phrase = _mode_phrase(mode, paused)
    elapsed_str = format_elapsed(elapsed_seconds)

    accent = _ACCENT_STYLE if use_color else None
    dim = _DIM_STYLE if use_color else None

    text = Text()
    text.append(f"{spinner_frame}  ")
    text.append("caffeine", style=accent)
    text.append(f" \u00b7 {phrase} \u00b7 {elapsed_str}")

    if duration_seconds is not None and not narrow:
        remaining = max(0, duration_seconds - elapsed_seconds)
        suffix = (
            f" \u00b7 {_format_duration(remaining)} / "
            f"{_format_duration(duration_seconds)} left"
        )
        text.append(suffix, style=dim)

    if show_quit_hint and not narrow:
        text.append(" \u00b7 q to quit", style=dim)

    return text
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_animations.py -v`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): add _build_status_text with narrow reflow and NO_COLOR"
```

---

## Task 6: Non-TTY path of `run_display` (TDD)

**Files:**
- Modify: `src/digital_caffeine/animations.py`
- Modify: `tests/test_animations.py`

- [ ] **Step 1: Add the failing test**

Append to `tests/test_animations.py`:

```python
from types import SimpleNamespace


class _FakeEngine:
    """Minimal stand-in for CaffeineEngine in tests."""

    def __init__(self, *, paused: bool = False, stop_after: float | None = None) -> None:
        self._paused = paused
        self._active = True
        self._stop_after = stop_after

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def is_active(self) -> bool:
        return self._active

    def stop_now(self) -> None:
        self._active = False


def test_run_display_non_tty_prints_one_line_and_waits(monkeypatch) -> None:
    from digital_caffeine.animations import run_display

    monkeypatch.setattr("sys.stdout.isatty", lambda: False)

    buf = StringIO()
    console = Console(file=buf, force_terminal=False, width=100)

    engine = _FakeEngine()

    # Stop the engine after a short delay on a background thread.
    import threading
    threading.Timer(0.1, engine.stop_now).start()

    run_display(engine=engine, mode=Mode.DISPLAY_ONLY, duration_seconds=None,
                console=console)

    output = buf.getvalue()
    assert "caffeine: keeping display awake" in output
    assert "Ctrl+C" in output
    # One-line fallback, not a multiline live block
    assert output.count("\n") <= 2
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_animations.py::test_run_display_non_tty_prints_one_line_and_waits -v`
Expected: `ImportError: cannot import name 'run_display'`.

- [ ] **Step 3: Implement `run_display` with non-TTY branch only**

Append to `src/digital_caffeine/animations.py`:

```python
import sys
import time

from rich.console import Console


def run_display(
    engine,
    mode: Mode,
    duration_seconds: int | None,
    *,
    console: Console | None = None,
) -> None:
    """Blocking display loop. Returns when the engine stops or user quits.

    - TTY: Rich Live redraw at FPS, reflows to terminal width.
    - Non-TTY (piped/redirected): prints one status line, then sleeps until
      the engine stops or Ctrl+C.
    """
    console = console or Console()

    if not sys.stdout.isatty():
        phrase = _MODE_PHRASES[mode]
        console.print(f"caffeine: {phrase} (press Ctrl+C to stop)")
        try:
            while engine.is_active:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    # TTY path implemented in Task 7.
    raise NotImplementedError("TTY path not yet implemented")
```

Move `import sys`, `import time`, and the `rich.console.Console` import to the top of the file.

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_animations.py -v`
Expected: all tests pass. The TTY branch is unreachable in automated tests.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat(animations): implement non-TTY fallback for run_display"
```

---

## Task 7: TTY path of `run_display` (manual smoke test)

**Files:**
- Modify: `src/digital_caffeine/animations.py`

No automated test in this task - the Rich Live loop + msvcrt key handler is verified manually. The pure functions it composes (`_build_status_text`, `_pick_quip`, `format_elapsed`) are already covered.

- [ ] **Step 1: Implement the TTY branch**

Replace the `raise NotImplementedError("TTY path not yet implemented")` line at the end of `run_display` with:

```python
    # TTY path
    use_color = os.environ.get("NO_COLOR") is None
    spinner_frames = ["\u280B", "\u2819", "\u2839", "\u2838", "\u283C", "\u2834",
                      "\u2826", "\u2827", "\u2807", "\u280F"]
    paused_frame = "\u2022"

    start = time.monotonic()
    spinner_idx = 0

    try:
        from rich.live import Live
        with Live(console=console, refresh_per_second=FPS, transient=False) as live:
            while engine.is_active:
                elapsed = int(time.monotonic() - start)
                if duration_seconds is not None and elapsed >= duration_seconds:
                    break

                paused = engine.is_paused
                frame = paused_frame if paused else spinner_frames[
                    spinner_idx % len(spinner_frames)
                ]
                width = console.size.width

                status = _build_status_text(
                    spinner_frame=frame,
                    mode=mode,
                    elapsed_seconds=elapsed,
                    duration_seconds=duration_seconds,
                    paused=paused,
                    width=width,
                    show_quit_hint=True,
                    use_color=use_color,
                )

                quip = _pick_quip(elapsed)
                quip_text = Text()
                if quip:
                    quip_text.append(f"    {quip}",
                                     style=_DIM_STYLE if use_color else None)

                block = Text()
                block.append_text(status)
                block.append("\n\n")
                block.append_text(quip_text)

                live.update(block)

                if _q_pressed():
                    break

                spinner_idx += 1
                time.sleep(1 / FPS)
    except KeyboardInterrupt:
        pass


def _q_pressed() -> bool:
    """Return True if 'q' or 'Q' was pressed since the last check.

    Uses msvcrt (Windows stdlib). On non-Windows platforms this returns False.
    """
    try:
        import msvcrt
    except ImportError:
        return False
    if msvcrt.kbhit():
        ch = msvcrt.getch()
        return ch in (b"q", b"Q")
    return False
```

- [ ] **Step 2: Run the existing test suite to confirm nothing regressed**

Run: `pytest tests/test_animations.py -v`
Expected: all tests still pass.

- [ ] **Step 3: Manual smoke test (critical)**

From a normal Windows terminal (not redirected), after running `pip install -e .`:

```bash
caffeine start --duration 20s
```

Verify:
1. Status line appears: `⠋  caffeine · keeping display + system awake · 0s · q to quit`
2. Spinner advances, elapsed ticks every second.
3. Duration suffix appears once it's meaningful: `· 0h 0m / 0h 0m left` (OK if this feels off - duration format is minute-granular by design, so short durations look blunt).
4. Around 5s, a quip line appears.
5. Resizing the terminal to narrow width (~40 cols) reflows and drops the quit hint + duration suffix.
6. Pressing `q` stops the engine cleanly.
7. Pressing Ctrl+C also stops cleanly.
8. On exit, a one-line summary prints (still from cli.py - Task 8 replaces the multi-line summary).

If any of the above fails, fix before committing.

- [ ] **Step 4: Smoke test NO_COLOR**

In a shell that supports env-var prefix (PowerShell or bash):

```bash
NO_COLOR=1 caffeine start --duration 10s
```

Verify no color codes appear. Status line is still present. Quip still appears.

- [ ] **Step 5: Smoke test non-TTY fallback**

```bash
caffeine start --duration 5s | cat
```

Verify one line prints: `caffeine: keeping display + system awake (press Ctrl+C to stop)`. No Live redraw. Engine stops on its own after 5s.

- [ ] **Step 6: Commit**

```bash
git add src/digital_caffeine/animations.py
git commit -m "feat(animations): implement TTY redraw loop with spinner and q-to-quit"
```

---

## Task 8: Rewrite `cli.py start` to use `run_display`

**Files:**
- Modify: `src/digital_caffeine/cli.py`

- [ ] **Step 1: Remove dead imports and helpers**

In `src/digital_caffeine/cli.py`, delete these entire blocks:

1. The import line importing `FPS`, `MODE_DISPLAY`, `build_animated_display`, `format_time` from `animations`. Replace with:
   ```python
   from digital_caffeine.animations import format_elapsed, run_display
   ```
2. The entire `build_display` function (currently around lines 70-92).
3. The entire `_can_use_pc98` function (currently around lines 95-101).
4. The entire `_run_rich_display` function (currently around lines 104-138).
5. The `from rich.live import Live` and `from rich.panel import Panel` imports (no longer used).

- [ ] **Step 2: Replace the CLI live-display block in `start`**

The current `start` function has (currently around lines 239-282):

```python
    start_time = time.monotonic()

    try:
        if _can_use_pc98():
            ...
        else:
            _run_rich_display(...)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        total_uptime = int(time.monotonic() - start_time)
        console.print()
        console.print("[bold cyan]Session Summary[/bold cyan]")
        console.print(f"  Total uptime:  {format_time(total_uptime)}")
        console.print(f"  Mode:          {MODE_DISPLAY[mode]}")
        if simulate:
            console.print("  Simulate:      On")
        console.print("[green]Digital Caffeine stopped. Sweet dreams![/green]")
```

Replace that entire block with:

```python
    start_time = time.monotonic()

    try:
        run_display(engine=engine, mode=mode, duration_seconds=duration_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        total_uptime = int(time.monotonic() - start_time)
        console.print(
            f"caffeine stopped \u00b7 kept awake for {format_elapsed(total_uptime)}"
        )
```

- [ ] **Step 3: Remove the pre-display "started" banner**

Also delete the line that currently prints `Digital Caffeine started - mode=...` inside `_run_rich_display` - that function is gone, so nothing to do here, but double-check no other `[green]Digital Caffeine started[/green]` print remains in `cli.py`. If one does, delete it.

- [ ] **Step 4: Run the CLI tests**

Run: `pytest tests/test_cli.py -v`
Expected: some tests fail because they still import `build_display` and `format_time` from `cli`. Those are fixed in Task 9.

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/cli.py
git commit -m "refactor(cli): replace PC-98/Rich dispatch with run_display"
```

---

## Task 9: Clean up `test_cli.py`

**Files:**
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Delete the dead imports and tests**

In `tests/test_cli.py`:

1. Change the import line:
   ```python
   from digital_caffeine.cli import build_display, cli, format_time, parse_duration
   ```
   to:
   ```python
   from digital_caffeine.cli import cli, parse_duration
   ```
2. Delete these tests entirely:
   - `test_format_time_zero`
   - `test_format_time_minutes_seconds`
   - `test_format_time_hours`
   - `test_build_display_returns_animated_panel`
3. Delete the unused imports at the top: `from io import StringIO`, `from rich.console import Console`, `from rich.panel import Panel`, `from digital_caffeine.constants import Mode` (only keep what's still used by remaining tests).

- [ ] **Step 2: Run the full test suite**

Run: `pytest -v`
Expected:
- All `test_animations.py` tests pass.
- All `test_cli.py` tests pass (parse_duration, version, config, start --help).
- `test_engine.py` and `test_config.py` unchanged and passing.
- `test_pc98_*.py` tests still exist and may be failing (pc98 package still present) - that's fine, they go in Task 10.

- [ ] **Step 3: Commit**

```bash
git add tests/test_cli.py
git commit -m "test(cli): drop tests for removed build_display and format_time"
```

---

## Task 10: Delete the `pc98` package and its tests

**Files:**
- Delete: `src/digital_caffeine/pc98/` (entire directory)
- Delete: `tests/test_pc98_canvas.py`
- Delete: `tests/test_pc98_palette.py`
- Delete: `tests/test_pc98_particles.py`
- Delete: `tests/test_pc98_scene.py`
- Delete: `tests/test_pc98_sprites.py`
- Delete: `tests/test_pc98_widgets.py`

- [ ] **Step 1: Delete the pc98 source package**

```bash
git rm -r src/digital_caffeine/pc98
```

- [ ] **Step 2: Delete the pc98 test files**

```bash
git rm tests/test_pc98_canvas.py tests/test_pc98_palette.py tests/test_pc98_particles.py tests/test_pc98_scene.py tests/test_pc98_sprites.py tests/test_pc98_widgets.py
```

- [ ] **Step 3: Confirm nothing else imports from `pc98`**

Run: `grep -r "digital_caffeine.pc98" src/ tests/` (via the Grep tool).
Expected: zero matches. If any, fix them.

- [ ] **Step 4: Run the full test suite**

Run: `pytest -v`
Expected: all remaining tests pass. Total test count drops by roughly 528 lines worth.

- [ ] **Step 5: Commit**

```bash
git commit -m "refactor: delete pc98 visual novel package and tests"
```

---

## Task 11: Remove `textual` from dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Remove the textual dependency line**

In `pyproject.toml`, change:

```toml
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pystray>=0.19",
    "Pillow>=10.0",
    "textual>=8.0",
]
```

to:

```toml
dependencies = [
    "click>=8.0",
    "rich>=13.0",
    "pystray>=0.19",
    "Pillow>=10.0",
]
```

- [ ] **Step 2: Re-install the package to refresh dependencies**

Run: `pip install -e ".[dev]"`
Expected: textual is either left installed (harmless) or removed. No errors.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "chore(deps): drop textual, no longer needed after pc98 removal"
```

---

## Task 12: Final verification

**Files:** none modified.

- [ ] **Step 1: Lint**

Run: `ruff check src/ tests/`
Expected: zero issues. If any appear in the new `animations.py` (e.g., unused imports left over from the incremental build), fix them with the Edit tool and re-run.

- [ ] **Step 2: Full test suite**

Run: `pytest -v`
Expected: all tests pass. Note the count for the commit message if anything changes.

- [ ] **Step 3: End-to-end smoke test**

Run these one after another, verifying behavior matches the spec:

1. `caffeine start --duration 15s` - minimal display, spinner, elapsed ticks, quip appears after ~5s, exits cleanly at 15s.
2. Resize terminal to ~40 cols during run - reflows, drops suffixes.
3. `NO_COLOR=1 caffeine start --duration 5s` - no color output.
4. `caffeine start --duration 3s | cat` - one-line non-TTY fallback.
5. `caffeine start --tray` - launches tray icon, unchanged from before. Right-click works, pause/resume/exit work. (If this breaks, there is a regression from deleted-symbol residue; investigate `tray.py` for any stray `animations` imports. Based on `tray.py:1-50` it does not import `animations`, so this should Just Work.)
6. `caffeine version` - prints version.
7. `caffeine config --show` - prints config or says "No config file found."

- [ ] **Step 4: Fix anything the smoke test surfaces**

If any step fails, debug at the source. Do NOT paper over with try/except or fallbacks; the spec's intent is simplification.

- [ ] **Step 5: Final commit (only if fixes were needed)**

If any fixes were made in this task:

```bash
git add <fixed-files>
git commit -m "fix: polish after end-to-end smoke test"
```

Otherwise this task ends with no commit.

---

## Done

At this point:
- `src/digital_caffeine/pc98/` is gone.
- `src/digital_caffeine/animations.py` is roughly 150-200 lines with one public `run_display` entry point.
- `tests/test_animations.py` is roughly 80-100 lines covering the pure helpers + non-TTY fallback.
- `pyproject.toml` no longer depends on `textual`.
- `caffeine start` shows a minimal, adaptive Claude-Code-style display.
- `caffeine start --tray`, `--simulate`, `--duration`, `--mode` all behave the same.
