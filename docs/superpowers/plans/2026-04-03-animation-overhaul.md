# Animation Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade CLI animations to 24 FPS with rainbow border, heat-shimmer steam, surface glow, drip particles, and handle breathing.

**Architecture:** All changes are in `animations.py`. Animation rates are decoupled from FPS using frame-count divisors. Pre-generated lookup tables for steam, border colors, and surface patterns. Deterministic drip particles via frame-seeded RNG.

**Tech Stack:** Python 3.10+, Rich (Panel, Style), math (sin, HSV conversion)

---

### Task 1: FPS Constant and Quip Timing

**Files:**
- Modify: `src/digital_caffeine/animations.py:14` (FPS), lines 362-384 (quip timing), line 335 (self-ref quip)
- Modify: `tests/test_animations.py` (quip timing tests)

- [ ] **Step 1: Update quip timing tests for 24 FPS**

In `tests/test_animations.py`, replace the quip tests that reference `8 * FPS` with `_QUIP_INTERVAL * FPS` pattern, and update for new timing (12 second interval, 1 char per 3 frames):

```python
def test_get_quip_rotates() -> None:
    frames_per_quip = 12 * FPS  # 12 seconds per quip at 24 FPS
    # Compare fully-typed quips at end of consecutive windows
    quip_a = get_quip(frame=frames_per_quip - 1, paused=False)
    quip_b = get_quip(frame=2 * frames_per_quip - 1, paused=False)
    assert quip_a != quip_b


def test_get_quip_typewriter_effect() -> None:
    # Frame 0 should show partial text (1 char + cursor)
    partial = get_quip(frame=0, paused=False)
    full = get_quip(frame=12 * FPS - 1, paused=False)
    assert len(partial) < len(full)
    assert full.startswith(partial[:1])


def test_get_quip_wraps_around() -> None:
    cycle_length = len(QUIPS) * 12 * FPS
    # Compare at same typing stage (fully typed)
    end = 12 * FPS - 1
    assert get_quip(frame=end, paused=False) == get_quip(
        frame=cycle_length + end, paused=False
    )
```

Also update the `build_animated_display` quip rotation test:

```python
def test_build_animated_display_quip_rotates() -> None:
    buf_0 = StringIO()
    console_0 = Console(file=buf_0, force_terminal=True, width=90)
    panel_0 = build_animated_display(
        frame=0,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_0.print(panel_0)

    buf_12 = StringIO()
    console_12 = Console(file=buf_12, force_terminal=True, width=90)
    panel_12 = build_animated_display(
        frame=12 * FPS,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=12,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    console_12.print(panel_12)

    assert buf_0.getvalue() != buf_12.getvalue()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_animations.py -k "quip" -v`
Expected: FAIL (timing mismatches since FPS is still 8)

- [ ] **Step 3: Update FPS, quip timing, and self-referential quip**

In `src/digital_caffeine/animations.py`:

Change line 14:
```python
FPS = 24
```

Change `_QUIP_INTERVAL` (line 362):
```python
_QUIP_INTERVAL = 12  # seconds per quip
```

Replace the `get_quip` function:
```python
def get_quip(frame: int, *, paused: bool) -> str:
    """Return the current quip with a typewriter reveal effect.

    Characters appear one at a time every 3 frames (~8 chars/sec at 24 FPS)
    with a blinking cursor while typing. Once fully revealed, the cursor
    disappears. Quip order is shuffled per-session.
    """
    if paused:
        return PAUSED_QUIP
    frames_per_quip = _QUIP_INTERVAL * FPS
    quip_idx = (frame // frames_per_quip) % len(QUIPS)
    quip = QUIPS[quip_idx]

    frame_in_quip = frame % frames_per_quip
    # 1 character every 3 frames = ~8 chars/sec at 24 FPS
    chars_to_show = min(len(quip), (frame_in_quip // 3) + 1)

    if chars_to_show < len(quip):
        cursor = "\u2588" if (frame % 18) < 9 else " "
        return quip[:chars_to_show] + cursor
    return quip
```

Update the self-referential quip (line 335):
```python
    "This animation runs at 24fps. You're welcome.",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -k "quip" -v`
Expected: All quip tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: bump FPS to 24 and adjust quip timing"
```

---

### Task 2: Rainbow Border

**Files:**
- Modify: `src/digital_caffeine/animations.py:187-215` (border color generation and getter)
- Modify: `tests/test_animations.py:77-89` (border tests)

- [ ] **Step 1: Update border tests for 72-step rainbow**

In `tests/test_animations.py`, replace the border tests:

```python
def test_border_colors_has_smooth_steps() -> None:
    assert len(BORDER_COLORS) == 72
    assert all(c.startswith("#") for c in BORDER_COLORS)


def test_get_border_color_cycles() -> None:
    # Border advances every 2 frames
    colors = [get_border_color(frame=i * 2, paused=False) for i in range(72)]
    assert colors == BORDER_COLORS
    assert get_border_color(frame=144, paused=False) == BORDER_COLORS[0]


def test_get_border_color_paused_returns_yellow() -> None:
    assert get_border_color(frame=0, paused=True) == "yellow"
    assert get_border_color(frame=99, paused=True) == "yellow"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_animations.py -k "border" -v`
Expected: FAIL (still 32 cyan steps)

- [ ] **Step 3: Replace border generation with HSV rainbow**

In `src/digital_caffeine/animations.py`, replace the entire border section (the `_generate_border_colors` function, `BORDER_COLORS`, and `get_border_color`):

```python
# -- Smooth HSV rainbow border (72-step hue rotation) ----------------------


def _hsv_to_hex(h: float, s: float, v: float) -> str:
    """Convert HSV (h: 0-360, s: 0-1, v: 0-1) to a hex color string."""
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0.0
    elif h < 120:
        r, g, b = x, c, 0.0
    elif h < 180:
        r, g, b = 0.0, c, x
    elif h < 240:
        r, g, b = 0.0, x, c
    elif h < 300:
        r, g, b = x, 0.0, c
    else:
        r, g, b = c, 0.0, x
    ri = int((r + m) * 255)
    gi = int((g + m) * 255)
    bi = int((b + m) * 255)
    return f"#{ri:02x}{gi:02x}{bi:02x}"


def _generate_border_colors(steps: int = 72) -> list[str]:
    """Generate a full HSV hue rotation at constant saturation and brightness.

    72 steps at S=0.7, V=0.85 for rich but not neon colors.
    Full rotation in ~6 seconds (advance every 2 frames at 24 FPS).
    """
    return [_hsv_to_hex(i * 360 / steps, 0.7, 0.85) for i in range(steps)]


BORDER_COLORS: list[str] = _generate_border_colors()


def get_border_color(frame: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Advances every 2 frames for a full rainbow rotation in ~6 seconds.
    """
    if paused:
        return "yellow"
    return BORDER_COLORS[(frame // 2) % len(BORDER_COLORS)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -k "border" -v`
Expected: All border tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: 72-step HSV rainbow border cycle"
```

---

### Task 3: Steam System Upgrade

**Files:**
- Modify: `src/digital_caffeine/animations.py:30-124` (steam constants, generation, getter)
- Modify: `tests/test_animations.py:27-48` (steam tests)

- [ ] **Step 1: Update steam tests for taller, denser system**

In `tests/test_animations.py`, replace the steam tests:

```python
def test_steam_frames_are_generated() -> None:
    assert len(STEAM_FRAMES) == 48


def test_get_steam_frame_cycles() -> None:
    first = get_steam_frame(frame=0, paused=False)
    # Steam advances every 3 frames, so full cycle is len * 3 frames
    wrapped = get_steam_frame(frame=len(STEAM_FRAMES) * 3, paused=False)
    assert first == wrapped


def test_get_steam_frame_has_seven_lines() -> None:
    result = get_steam_frame(frame=0, paused=False)
    assert len(result.split("\n")) == 7


def test_get_steam_frame_paused_returns_blank_lines() -> None:
    result = get_steam_frame(frame=0, paused=True)
    lines = result.split("\n")
    assert len(lines) == 7
    assert all(line.strip() == "" for line in lines)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_animations.py -k "steam" -v`
Expected: FAIL (still 24 frames, 5 lines)

- [ ] **Step 3: Rewrite steam system**

In `src/digital_caffeine/animations.py`, replace the steam section (from `_STEAM_WIDTH` through `get_steam_frame`):

```python
# -- Procedural steam generation with warm-to-cool gradient ----------------

_STEAM_WIDTH = 25
_STEAM_HEIGHT = 7

# Warm near cup (bottom rows), cooling to gray as steam rises (top rows)
_WISP_COLORS = [
    "#444444",  # row 0 (top) - nearly invisible
    "#555555",  # row 1
    "#666666",  # row 2
    "#888888",  # row 3 - mid gray
    "#997755",  # row 4 - warm tan
    "#AA8866",  # row 5 - warm brown-tan
    "#AA8866",  # row 6 (bottom, near cup) - warmest
]
_TRAIL_COLORS = [
    "#303030",
    "#383838",
    "#444444",
    "#555555",
    "#776655",
    "#886644",
    "#886644",
]

# Heat shimmer characters and colors for bottom 2 rows
_SHIMMER_CHARS = ["*", "\u00b7", "'"]
_SHIMMER_COLORS = ["#FFB347", "#FFA500", "#FF8C00"]


def _generate_steam_frames() -> list[str]:
    """Generate 48 steam frames with warm-to-cool gradient and heat shimmer.

    Wisps start warm near the cup and cool to gray as they rise.
    Occasional shimmer characters appear near the cup in warm orange/gold.
    """
    cx = 12
    num_frames = 48
    age_chars = [")", "~", "'", "\u00b7", ".", "\u00b7", "'"]
    trail_chars = ["~", "'", "\u00b7", ".", " ", " ", " "]
    max_age = 9

    wisps = [
        (0, cx - 2, 1.2, 0.50),
        (1, cx + 1, 1.0, 0.40),
        (2, cx, 0.8, 0.60),
        (3, cx - 1, 1.5, 0.30),
        (4, cx + 2, 1.1, 0.50),
        (5, cx - 3, 0.9, 0.70),
        (6, cx + 1, 1.3, 0.40),
        (0, cx + 3, 0.7, 0.35),
        (3, cx - 3, 1.0, 0.55),
        (5, cx + 2, 1.4, 0.45),
        (1, cx - 4, 1.1, 0.65),
        (7, cx + 3, 0.9, 0.50),
        (2, cx - 1, 1.6, 0.35),
        (4, cx, 0.7, 0.75),
        (6, cx - 2, 1.3, 0.55),
    ]

    frames = []
    for f in range(num_frames):
        char_grid = [[" "] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]
        color_grid = [[None] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]

        for birth, bx, amp, freq in wisps:
            age = (f - birth) % max_age
            row = _STEAM_HEIGHT - 1 - age
            drift = math.sin(f * freq + birth * 0.9) * amp
            x = int(round(bx + drift))

            if 0 <= row < _STEAM_HEIGHT:
                char = age_chars[min(age, len(age_chars) - 1)]
                color = _WISP_COLORS[min(row, len(_WISP_COLORS) - 1)]
                if 0 <= x < _STEAM_WIDTH and char_grid[row][x] == " ":
                    char_grid[row][x] = char
                    color_grid[row][x] = color

            # Trail: one row below, fainter
            tr = row + 1
            if 0 <= tr < _STEAM_HEIGHT and age > 0:
                tc = trail_chars[min(age - 1, len(trail_chars) - 1)]
                tcol = _TRAIL_COLORS[min(tr, len(_TRAIL_COLORS) - 1)]
                tx = int(round(bx + drift * 0.6))
                if (
                    tc != " "
                    and 0 <= tx < _STEAM_WIDTH
                    and char_grid[tr][tx] == " "
                ):
                    char_grid[tr][tx] = tc
                    color_grid[tr][tx] = tcol

        # Heat shimmer in bottom 2 rows
        shimmer_seed = f * 7 + 13
        for row in range(_STEAM_HEIGHT - 2, _STEAM_HEIGHT):
            # Deterministic pseudo-random shimmer
            sx = (shimmer_seed * (row + 1) * 31) % _STEAM_WIDTH
            if char_grid[row][sx] == " " and (shimmer_seed + row) % 5 < 2:
                si = (shimmer_seed + row) % len(_SHIMMER_CHARS)
                char_grid[row][sx] = _SHIMMER_CHARS[si]
                color_grid[row][sx] = _SHIMMER_COLORS[si]

        # Render with per-character markup
        frame_lines = []
        for y in range(_STEAM_HEIGHT):
            line = ""
            for x in range(_STEAM_WIDTH):
                c = char_grid[y][x]
                col = color_grid[y][x]
                if c != " " and col:
                    line += f"[{col}]{c}[/]"
                else:
                    line += c
            frame_lines.append(line)
        frames.append("\n".join(frame_lines))
    return frames


STEAM_FRAMES: list[str] = _generate_steam_frames()


def get_steam_frame(frame: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Warm wisps near the cup cool to gray as they rise. Heat shimmer
    sparkles in orange/gold near the cup mouth. Steam advances every
    3 display frames for natural rising speed at 24 FPS.
    """
    if paused:
        return "\n".join([" " * _STEAM_WIDTH] * _STEAM_HEIGHT)
    sf = (frame // 3) % len(STEAM_FRAMES)
    return STEAM_FRAMES[sf]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -k "steam" -v`
Expected: All steam tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: taller steam with warm-to-cool gradient and heat shimmer"
```

---

### Task 4: Liquid Surface Enhancement

**Files:**
- Modify: `src/digital_caffeine/animations.py:127-181` (surface patterns, cup art)
- Modify: `tests/test_animations.py:53-72` (cup art tests)

- [ ] **Step 1: Add test for surface glow color changes**

In `tests/test_animations.py`, add a new test after the existing cup tests:

```python
def test_get_cup_art_surface_glow_shifts() -> None:
    """Surface color oscillates over time, so distant frames differ."""
    art_0 = get_cup_art(frame=0, paused=False)
    # ~2 seconds later at 24 FPS = 48 frames, should be at a different glow phase
    art_48 = get_cup_art(frame=48, paused=False)
    assert art_0 != art_48
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_animations.py -k "surface_glow" -v`
Expected: FAIL (surface patterns repeat in a short cycle without glow)

- [ ] **Step 3: Rewrite surface patterns and cup art with glow + shimmer**

In `src/digital_caffeine/animations.py`, replace the cup art section (from `_SURFACE_PATTERNS` through `get_cup_art`):

```python
# -- Cup art with animated liquid surface, glow, and shimmer ----------------

# 16 ripple patterns (characters only - color applied dynamically)
_SURFACE_CHARS: list[str] = [
    "~\u2248~\u2248~\u2248~\u2248~\u2248~",
    "~\u2248\u2248~\u2248~\u2248\u2248~\u2248~",
    "\u2248~\u2248~\u2248~\u2248~\u2248~\u2248",
    "\u2248~\u2248\u2248~\u2248\u2248~\u2248~\u2248",
    "\u2248~~\u2248~~\u2248~~\u2248~",
    "~\u2248\u2248~\u2248\u2248~\u2248\u2248~\u2248",
    "~\u2248~\u2248\u2248~\u2248~\u2248~\u2248",
    "\u2248~\u2248~\u2248\u2248~\u2248~\u2248~",
    "~\u2248~\u2248~\u2248~\u2248\u2248~\u2248",
    "\u2248\u2248~\u2248~\u2248~\u2248~\u2248~",
    "~\u2248\u2248~\u2248~\u2248\u2248~\u2248\u2248",
    "\u2248~\u2248\u2248~\u2248~\u2248~\u2248~",
    "~\u2248~\u2248\u2248\u2248~\u2248~\u2248~",
    "\u2248~\u2248~\u2248~\u2248\u2248\u2248~\u2248",
    "\u2248\u2248~\u2248~~\u2248~\u2248\u2248~",
    "~\u2248\u2248\u2248~\u2248~\u2248~\u2248~",
]


def _surface_color(frame: int) -> str:
    """Return the surface color for the current frame.

    Oscillates between chocolate (#D2691E) and warm gold (#FFB347)
    using sine interpolation over ~4 seconds.
    """
    t = (math.sin(frame / (4 * FPS) * 2 * math.pi) + 1) / 2
    # Interpolate RGB: #D2691E -> #FFB347
    r = int(0xD2 + t * (0xFF - 0xD2))
    g = int(0x69 + t * (0xB3 - 0x69))
    b = int(0x1E + t * (0x47 - 0x1E))
    return f"#{r:02x}{g:02x}{b:02x}"


def _surface_with_shimmer(frame: int) -> str:
    """Build the animated surface line with color glow and shimmer highlights.

    1-2 positions per frame get a gold highlight for light-catching effect.
    """
    pattern_idx = (frame // 3) % len(_SURFACE_CHARS)
    chars = list(_SURFACE_CHARS[pattern_idx])
    color = _surface_color(frame)

    # Deterministic shimmer: replace 1-2 chars with gold highlights
    shimmer_seed = frame * 17 + 7
    for i in range(2):
        pos = (shimmer_seed + i * 11) % len(chars)
        if (shimmer_seed + i) % 7 < 3:
            chars[pos] = "*" if i == 0 else "'"

    # Build markup: shimmer chars get gold, rest get glow color
    result = ""
    for j, ch in enumerate(chars):
        if ch in ("*", "'"):
            result += f"[#FFD700]{ch}[/]"
        else:
            result += f"[{color}]{ch}[/]"
    return result


# Pre-built cup components with hex color gradient
_CUP_TOP = "     [white]\u250c" + "\u2500" * 13 + "\u2510[/]    "
_CUP_BOT = "     [white]\u2514" + "\u2500" * 13 + "\u2518[/]    "
_CUP_SAUCER = "    [#555555]" + "\u2550" * 19 + "[/]  "
_CUP_DIM = "[dim]" + "\u2591" * 11 + "[/]"
_CUP_FILL_1 = "[#B8520A]" + "\u2592" * 11 + "[/]"
_CUP_FILL_2 = "[#8B4513]" + "\u2593" * 11 + "[/]"
_CUP_FILL_3 = "[#5C2E0E]" + "\u2593" * 11 + "[/]"

# Pre-cached paused cup (never changes)
_CUP_PAUSED: str = "\n".join([
    _CUP_TOP,
    f"     [white]\u2502[/] {_CUP_DIM} [white]\u251c\u2500\u2500\u256e[/]",
    f"     [white]\u2502[/] {_CUP_DIM} [white]\u2502[/]  [white]\u2502[/]",
    f"     [white]\u2502[/] {_CUP_DIM} [white]\u2502[/]  [white]\u2502[/]",
    f"     [white]\u2502[/] {_CUP_DIM} [white]\u251c\u2500\u2500\u256f[/]",
    _CUP_BOT,
    _CUP_SAUCER,
])


def get_cup_art(frame: int, *, paused: bool) -> str:
    """Return the coffee cup ASCII art for the current frame.

    Active cups show a 4-step brown gradient with an animated liquid
    ripple that glows between chocolate and gold. Shimmer highlights
    catch the light. Handle breathes in sync with border cycle.
    """
    if paused:
        return _CUP_PAUSED

    surface = _surface_with_shimmer(frame)

    # Handle breathing: cycle between white and dim white in sync with border
    handle_phase = (frame // 2) % 72  # same cycle as border
    ht = (math.sin(handle_phase / 72 * 2 * math.pi) + 1) / 2
    hv = int(170 + ht * 85)  # #AAAAAA to #FFFFFF
    hcolor = f"#{hv:02x}{hv:02x}{hv:02x}"

    lines = [
        _CUP_TOP,
        f"     [white]\u2502[/] {surface} [{hcolor}]\u251c\u2500\u2500\u256e[/]",
        f"     [white]\u2502[/] {_CUP_FILL_1} [{hcolor}]\u2502[/]  [{hcolor}]\u2502[/]",
        f"     [white]\u2502[/] {_CUP_FILL_2} [{hcolor}]\u2502[/]  [{hcolor}]\u2502[/]",
        f"     [white]\u2502[/] {_CUP_FILL_3} [{hcolor}]\u251c\u2500\u2500\u256f[/]",
        _CUP_BOT,
        _CUP_SAUCER,
    ]
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -k "cup" -v`
Expected: All cup tests PASS (including the new glow test)

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: 16-pattern surface with glow oscillation, shimmer highlights, handle breathing"
```

---

### Task 5: Coffee Drip Particles

**Files:**
- Modify: `src/digital_caffeine/animations.py` (add drip system, modify `build_animated_display`)
- Modify: `tests/test_animations.py` (add drip tests)

- [ ] **Step 1: Add drip particle tests**

In `tests/test_animations.py`, add imports and tests. First update the imports at the top:

```python
from digital_caffeine.animations import (
    BORDER_COLORS,
    FPS,
    PAUSED_QUIP,
    QUIPS,
    STEAM_FRAMES,
    build_animated_display,
    get_border_color,
    get_cup_art,
    get_drip_particles,
    get_quip,
    get_steam_frame,
)
```

Then add drip tests before the `build_animated_display` section:

```python
# -- Drip particle tests --


def test_get_drip_particles_returns_list() -> None:
    drips = get_drip_particles(frame=0)
    assert isinstance(drips, list)


def test_get_drip_particles_max_two() -> None:
    # Check across many frames that we never exceed 2 active drips
    for f in range(500):
        drips = get_drip_particles(frame=f)
        assert len(drips) <= 2


def test_get_drip_particles_deterministic() -> None:
    """Same frame number always produces the same drips."""
    a = get_drip_particles(frame=100)
    b = get_drip_particles(frame=100)
    assert a == b
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_animations.py -k "drip" -v`
Expected: FAIL (get_drip_particles does not exist)

- [ ] **Step 3: Implement drip particle system**

In `src/digital_caffeine/animations.py`, add this section after the cup art section (before the border section):

```python
# -- Coffee drip particles -------------------------------------------------

# Drip spawn columns (within cup walls, columns 6-16 in art space)
_DRIP_COLS = list(range(6, 17))
_DRIP_COLORS = ["#B8520A", "#A0460E", "#8B4513"]


def get_drip_particles(frame: int) -> list[tuple[int, int, str, str]]:
    """Return active drip particles as (row_offset, col, char, color) tuples.

    Drips spawn deterministically based on frame number. Each drip falls
    1-2 rows over 6-10 frames. Max 2 active at once. row_offset is
    relative to just below the cup (0 = first row under saucer).

    Returns a list of (row_offset, col, character, color) tuples.
    """
    drips: list[tuple[int, int, str, str]] = []

    # Check recent spawn windows for active drips
    # Spawn window: one potential drip every ~60 frames (~2.5s at 24 FPS)
    spawn_interval = 60
    lifespan = 8  # frames a drip lives

    for window in range(3):  # check last 3 spawn windows
        spawn_frame = ((frame // spawn_interval) - window) * spawn_interval
        if spawn_frame < 0:
            continue

        # Deterministic spawn decision
        seed = spawn_frame * 31 + 17
        if seed % 5 < 2:  # ~40% chance per window
            age = frame - spawn_frame
            if 0 <= age < lifespan:
                col = _DRIP_COLS[seed % len(_DRIP_COLS)]
                row = age // 3  # fall 1 row every 3 frames
                ci = min(age // 3, len(_DRIP_COLORS) - 1)
                char = "'" if age < lifespan // 2 else "."
                drips.append((row, col, char, _DRIP_COLORS[ci]))

        if len(drips) >= 2:
            break

    return drips[:2]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_animations.py -k "drip" -v`
Expected: All drip tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: deterministic coffee drip particle system"
```

---

### Task 6: Integrate Drips into Display Assembly

**Files:**
- Modify: `src/digital_caffeine/animations.py:418-502` (`build_animated_display`)
- Modify: `tests/test_animations.py` (integration test)

- [ ] **Step 1: Add integration test for drip rendering**

In `tests/test_animations.py`, add:

```python
def test_build_animated_display_renders_without_error_at_many_frames() -> None:
    """Verify display assembly works at various frame counts without crashing."""
    for f in [0, 1, 24, 48, 100, 288, 500]:
        panel = build_animated_display(
            frame=f,
            mode=Mode.DISPLAY_AND_SYSTEM,
            uptime_seconds=f // FPS,
            duration_seconds=None,
            interval=60,
            paused=False,
            simulate=False,
        )
        assert isinstance(panel, Panel)
```

- [ ] **Step 2: Run test to verify it passes (baseline)**

Run: `pytest tests/test_animations.py -k "renders_without_error" -v`
Expected: PASS (current code already works, this is a safety net for the integration change)

- [ ] **Step 3: Add drip particles to display assembly**

In `src/digital_caffeine/animations.py`, update `build_animated_display`. Replace the display assembly function:

```python
def build_animated_display(
    *,
    frame: int,
    mode: Mode,
    uptime_seconds: int,
    duration_seconds: int | None,
    interval: int,
    paused: bool,
    simulate: bool,
) -> Panel:
    """Build an animated Rich Panel showing keep-awake status with coffee art.

    Status fields are vertically centered beside the cup art. Drip particles
    render below the saucer. A progress bar appears when a duration is set.
    """
    steam = get_steam_frame(frame, paused=paused)
    cup = get_cup_art(frame, paused=paused)
    border_color = get_border_color(frame, paused=paused)
    quip = get_quip(frame, paused=paused)

    status_str = (
        "[yellow]Paused[/yellow]" if paused else "[green]Active[/green]"
    )

    if duration_seconds is not None:
        remaining = max(0, duration_seconds - uptime_seconds)
        remaining_str = format_time(remaining)
    else:
        remaining_str = "Indefinite"

    sim_str = "[green]On[/green]" if simulate else "[dim]Off[/dim]"

    steam_lines = steam.split("\n")
    cup_lines = cup.split("\n")

    # Drip particle rows (below saucer)
    drip_lines: list[str] = []
    if not paused:
        drips = get_drip_particles(frame)
        if drips:
            # 2 rows of drip space
            drip_grid = [[" "] * _STEAM_WIDTH for _ in range(2)]
            drip_color_grid: list[list[str | None]] = [[None] * _STEAM_WIDTH for _ in range(2)]
            for row_off, col, char, color in drips:
                if 0 <= row_off < 2 and 0 <= col < _STEAM_WIDTH:
                    drip_grid[row_off][col] = char
                    drip_color_grid[row_off][col] = color
            for y in range(2):
                line = ""
                for x in range(_STEAM_WIDTH):
                    c = drip_grid[y][x]
                    col = drip_color_grid[y][x]
                    if c != " " and col:
                        line += f"[{col}]{c}[/]"
                    else:
                        line += c
                drip_lines.append(line)

    art_lines = steam_lines + cup_lines + drip_lines

    status_fields = [
        f"Status:         {status_str}",
        f"Mode:           {MODE_DISPLAY.get(mode, str(mode))}",
        f"Uptime:         {format_time(uptime_seconds)}",
        f"Time remaining: {remaining_str}",
        f"Interval:       {interval}s",
        f"Simulate:       {sim_str}",
    ]

    if duration_seconds is not None:
        status_fields.append("")
        status_fields.append(
            _build_progress_bar(uptime_seconds, duration_seconds)
        )

    # Vertically center status beside the art
    status_offset = (len(art_lines) - len(status_fields)) // 2
    status_offset = max(0, status_offset)

    art_width = 28
    combined_lines: list[str] = []
    total_rows = max(len(art_lines), len(status_fields) + status_offset)
    for i in range(total_rows):
        left = art_lines[i] if i < len(art_lines) else ""
        si = i - status_offset
        right = ""
        if 0 <= si < len(status_fields):
            right = status_fields[si]
        combined_lines.append(f" {_pad_to(left, art_width)} {right}")

    combined_lines.append("")
    if paused:
        combined_lines.append(
            f" [yellow dim italic]{quip}[/yellow dim italic]"
        )
    else:
        combined_lines.append(f" [dim italic]{quip}[/dim italic]")

    combined_lines.append("")
    combined_lines.append(" [dim]Press Ctrl+C to stop[/dim]")

    content = "\n".join(combined_lines)
    return Panel(
        content,
        title="[bold cyan]:coffee: Digital Caffeine[/bold cyan]",
        border_style=Style(color=border_color),
        padding=(1, 1),
        expand=False,
    )
```

- [ ] **Step 4: Run full test suite**

Run: `pytest tests/test_animations.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/digital_caffeine/animations.py tests/test_animations.py
git commit -m "feat: integrate drip particles into display assembly"
```

---

### Task 7: Full Test Suite and Border Color Stability Test

**Files:**
- Modify: `tests/test_animations.py` (final border style test fix)

- [ ] **Step 1: Fix border style change test**

The existing test `test_build_animated_display_border_color_changes` asserts that frame 0 and frame 1 have different border styles. With the new `frame // 2` advance, frames 0 and 1 will have the SAME border color. Update to compare frames 0 and 2:

```python
def test_build_animated_display_border_color_changes() -> None:
    panel_0 = build_animated_display(
        frame=0,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    panel_2 = build_animated_display(
        frame=2,
        mode=Mode.DISPLAY_AND_SYSTEM,
        uptime_seconds=0,
        duration_seconds=None,
        interval=60,
        paused=False,
        simulate=False,
    )
    assert panel_0.border_style != panel_2.border_style
```

- [ ] **Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: ALL tests PASS across all test files

- [ ] **Step 3: Run linter**

Run: `ruff check src/digital_caffeine/animations.py tests/test_animations.py`
Expected: No lint errors

- [ ] **Step 4: Commit**

```bash
git add tests/test_animations.py
git commit -m "fix: update border style test for 2-frame advance rate"
```

---

### Task 8: Visual Smoke Test

**Files:** None modified - manual verification only.

- [ ] **Step 1: Run the app in simulate mode to visually verify**

Run: `caffeine start --simulate --duration 30s`

Verify visually:
- Steam is taller (7 rows), warm-colored near cup, gray at top
- Orange shimmer sparkles appear near cup mouth
- Coffee surface glows between brown and gold
- Shimmer highlights (`*`, `'`) appear on liquid
- Handle breathes between white and gray
- Border cycles through full rainbow spectrum
- Occasional drip particles fall below saucer
- Quips type out at a deliberate pace (~8 chars/sec)
- Everything feels smooth at 24 FPS

- [ ] **Step 2: Final commit with version note**

```bash
git add -A
git commit -m "feat: animation overhaul - 24fps, rainbow border, heat shimmer, surface glow, drip particles"
```

Only needed if there are any stray changes from the visual test. If working tree is clean, skip this step.

---

### Spec Deviation Note

The spec mentions "brightest wisps (bottom row) tint toward the current border hue." This is intentionally omitted because it would require making steam frames dynamic rather than pre-generated, which is a significant architecture change for a subtle effect. The warm-to-cool gradient already gives the bottom wisps distinct character. This can be revisited as a follow-up if desired.
