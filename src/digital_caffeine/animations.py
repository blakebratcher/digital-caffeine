"""Animation data and helpers for the Digital Caffeine CLI display."""

from __future__ import annotations

import math
import re

from rich.panel import Panel
from rich.style import Style

from digital_caffeine.constants import Mode

# -- Configuration -----------------------------------------------------------

FPS = 8

# -- Markup-aware layout helpers ---------------------------------------------


def _visible_len(s: str) -> int:
    """Return visible character count, ignoring Rich markup tags."""
    return len(re.sub(r"\[/?[^\]]*\]", "", s))


def _pad_to(s: str, width: int) -> str:
    """Pad string to target visible width, accounting for Rich markup."""
    return s + " " * max(0, width - _visible_len(s))


# -- Procedural steam generation ---------------------------------------------

_STEAM_WIDTH = 25
_STEAM_HEIGHT = 5


def _generate_steam_frames() -> list[str]:
    """Generate smooth steam animation frames with rising wisps and trails."""
    cx = 12
    num_frames = 24
    age_chars = [")", "~", "'", "\u00b7", "."]
    trail_chars = ["~", "'", "\u00b7", ".", " "]
    max_age = 7

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
    ]

    frames = []
    for f in range(num_frames):
        grid = [[" "] * _STEAM_WIDTH for _ in range(_STEAM_HEIGHT)]
        for birth, bx, amp, freq in wisps:
            age = (f - birth) % max_age
            row = _STEAM_HEIGHT - 1 - age
            drift = math.sin(f * freq + birth * 0.9) * amp
            x = int(round(bx + drift))
            if 0 <= row < _STEAM_HEIGHT:
                char = age_chars[min(age, len(age_chars) - 1)]
                if 0 <= x < _STEAM_WIDTH and grid[row][x] == " ":
                    grid[row][x] = char
            tr = row + 1
            if 0 <= tr < _STEAM_HEIGHT and age > 0:
                tc = trail_chars[min(age - 1, len(trail_chars) - 1)]
                tx = int(round(bx + drift * 0.6))
                if (
                    tc != " "
                    and 0 <= tx < _STEAM_WIDTH
                    and grid[tr][tx] == " "
                ):
                    grid[tr][tx] = tc
        frames.append("\n".join("".join(row) for row in grid))
    return frames


STEAM_FRAMES: list[str] = _generate_steam_frames()


def get_steam_frame(frame: int, *, paused: bool) -> str:
    """Return the steam art for the current frame.

    Steam advances at half the display FPS for natural rising speed.
    """
    if paused:
        return "\n".join([" " * _STEAM_WIDTH] * _STEAM_HEIGHT)
    sf = (frame // 2) % len(STEAM_FRAMES)
    raw = STEAM_FRAMES[sf]
    return "\n".join(f"[dim]{line}[/]" for line in raw.split("\n"))


# -- Cup art with animated liquid surface ------------------------------------

_SURFACE_PATTERNS: list[str] = [
    "[#D2691E]~\u2248~\u2248~\u2248~\u2248~\u2248~[/]",
    "[#D2691E]~\u2248\u2248~\u2248~\u2248\u2248~\u2248~[/]",
    "[#D2691E]\u2248~\u2248~\u2248~\u2248~\u2248~\u2248[/]",
    "[#D2691E]\u2248~\u2248\u2248~\u2248\u2248~\u2248~\u2248[/]",
    "[#D2691E]\u2248~~\u2248~~\u2248~~\u2248~[/]",
    "[#D2691E]~\u2248\u2248~\u2248\u2248~\u2248\u2248~\u2248[/]",
    "[#D2691E]~\u2248~\u2248\u2248~\u2248~\u2248~\u2248[/]",
    "[#D2691E]\u2248~\u2248~\u2248\u2248~\u2248~\u2248~[/]",
]

# Pre-built cup components
_CUP_TOP = "     [white]\u250c" + "\u2500" * 13 + "\u2510[/]    "
_CUP_BOT = "     [white]\u2514" + "\u2500" * 13 + "\u2518[/]    "
_CUP_SAUCER = "    [dim]" + "\u2550" * 19 + "[/]  "
_CUP_DIM = "[dim]" + "\u2591" * 11 + "[/]"
_CUP_MED = "[#A0522D]" + "\u2592" * 11 + "[/]"
_CUP_DARK = "[#6B4226]" + "\u2593" * 11 + "[/]"

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

    Active cups have a brown gradient with an animated liquid ripple
    and white outline. Paused cups show dimmed fill (pre-cached).
    """
    if paused:
        return _CUP_PAUSED
    surface = _SURFACE_PATTERNS[
        (frame // 2) % len(_SURFACE_PATTERNS)
    ]
    lines = [
        _CUP_TOP,
        f"     [white]\u2502[/] {surface} [white]\u251c\u2500\u2500\u256e[/]",
        f"     [white]\u2502[/] {_CUP_MED} [white]\u2502[/]  [white]\u2502[/]",
        f"     [white]\u2502[/] {_CUP_DARK} [white]\u2502[/]  [white]\u2502[/]",
        f"     [white]\u2502[/] {_CUP_DARK} [white]\u251c\u2500\u2500\u256f[/]",
        _CUP_BOT,
        _CUP_SAUCER,
    ]
    return "\n".join(lines)


# -- Border colors (8-step breathing cycle) ----------------------------------

BORDER_COLORS: list[str] = [
    "bright_cyan",
    "cyan",
    "dark_cyan",
    "dark_cyan",
    "dark_cyan",
    "cyan",
    "bright_cyan",
    "cyan",
]


def get_border_color(frame: int, *, paused: bool) -> str:
    """Return the border color for the current frame.

    Changes twice per second for a smooth breathing effect.
    """
    if paused:
        return "yellow"
    step = max(1, FPS // 2)
    return BORDER_COLORS[(frame // step) % len(BORDER_COLORS)]


# -- Quips with typewriter effect --------------------------------------------

_ALL_QUIPS: list[str] = [
    # -- coffee puns --
    "Brewing productivity...",
    "Espresso yourself freely",
    "A latte work getting done today",
    "Grounds for staying awake",
    "Bean there, done that",
    "Mocha your day productive",
    "Don't lose your tamper",
    "Brew-tally efficient",
    "Affogato what sleep feels like",
    "Pour decisions? Never heard of 'em",
    "Words cannot espresso how awake this PC is",
    "Better latte than never",
    "You mocha me crazy",
    "Sip happens",
    "Thanks a latte",
    "I like big mugs and I cannot lie",
    "Rise and grind",
    "Life begins after coffee",
    "Deja brew: you've had this coffee before",
    "Brew can do it",
    "What's brewin', good lookin'?",
    "Mugs and kisses",
    "The daily grind, literally",
    "Java the Hutt would be proud",
    "No filter needed",
    "Keep calm and drink coffee",
    "Frappe-ning right now: productivity",
    "Cold brew? Never. Hot and alert.",
    "Percolating at maximum efficiency",
    "Another shot? Don't mind if I do",
    "Brewtiful day to stay awake",
    "I've bean thinking about staying awake",
    "Instant coffee is an oxymoron, like instant sleep",
    "Drip, drip, drip... staying awake",
    # -- sleep/awake --
    "Sleep is for the weak (and not this PC)",
    "Your PC refuses to sleep",
    "This machine has a no-nap policy",
    "Insomnia, but make it productive",
    "Your PC is more awake than you are",
    "Counting sheep? This PC doesn't know what sheep are",
    "The only thing sleeping here is your screensaver",
    "This PC runs on pure spite and caffeine",
    "Sleep.exe has been permanently uninstalled",
    "Who needs sleep when you have caffeine?",
    "Power nap? More like power no",
    "This machine hasn't blinked in hours",
    "ZZZ? Not on my watch",
    "Your PC is an insomniac and it's proud",
    "The sandman was denied entry",
    "Wide awake and slightly jittery",
    "No rest for the wicked (or this PC)",
    "Yawning is contagious. Good thing PCs can't yawn.",
    "This PC pulled an all-nighter",
    "Your PC's alarm clock is unnecessary",
    "Lullabies have no power here",
    "Naptime? We don't do that here",
    "Your PC passed the vibe check: awake",
    # -- tech humor --
    "SetThreadExecutionState goes brrr",
    "Keeping the electrons flowing",
    "sudo keep-awake --force --forever",
    "while(true) { stayAwake(); }",
    "Your screensaver is filing a complaint",
    "Power management has left the chat",
    "The screen shall not dim",
    "Task Manager can't stop what it can't see",
    "Your IT admin would not approve",
    "404: Sleep Not Found",
    "Have you tried turning it off and... no. Absolutely not.",
    "This violates at least three energy policies",
    "Connection to sleep server: REFUSED",
    "The power settings have been politely overruled",
    "Kernel panic? More like kernel party",
    "Running hot, staying cool",
    "This process has elevated privileges (to party)",
    "Uptime is the only metric that matters",
    "ping localhost: awake, awake, awake",
    "Thread status: caffeinated",
    "Garbage collection? Not collecting this process",
    "Exception: SleepNotAllowedException",
    "Runtime: forever. Or until Ctrl+C.",
    "Memory leak? No, memory feature",
    # -- workplace --
    "Look busy, stay caffeinated",
    "Your Teams status: permanently green",
    "Productivity level: caffeinated",
    "HR can't prove you weren't at your desk",
    "Working hard or hardly sleeping?",
    "Annual review: never falls asleep on the job",
    "If anyone asks, you've been here the whole time",
    "Meeting in 5. Good thing the screen's still on.",
    "The screensaver is on unpaid leave",
    "This PC is doing the bare minimum... perfectly",
    "Corporate wants you to keep working. PC agrees.",
    "PTO stands for PC Turned On",
    # -- absurd --
    "Somewhere, a bear is jealous of your lack of hibernation",
    "Running on vibes and voltage",
    "The void stares back, but at least the screen is on",
    "Your PC has evolved beyond the need for rest",
    "Powered by caffeine and questionable decisions",
    "The coffee is a metaphor. The wakefulness is literal.",
    "One does not simply let Windows sleep",
    "Instructions unclear, PC now runs on coffee",
    "Your PC's spirit animal is an owl on espresso",
    "In a parallel universe, this PC is napping",
    "This is fine. Everything is fine.",
    "Schrödinger's PC: simultaneously asleep and awake. JK, it's awake.",
    "The mitochondria is the powerhouse. Caffeine is the keep-awake.",
    "Time is an illusion. Uptime doubly so.",
    "Your PC has transcended the sleep-wake cycle",
    # -- self-referential --
    "This animation runs at 8fps. You're welcome.",
    "Handcrafted artisan wakefulness",
    "Small program, big dreams",
    "Still here. Still awake. Still caffeinated.",
    "Keeping it real (and awake)",
    "Just doing my job over here",
    "Your PC is caffeinated",
    "Freshly brewed and wide awake",
    "No decaf allowed here",
    "This machine runs on caffeine",
    "Another cup? Don't mind if I do",
    "Keeping things percolating...",
]

# Shuffle per-session so each launch feels different
def _shuffle_quips() -> list[str]:
    import os
    import random
    rng = random.Random(os.getpid())
    return rng.sample(_ALL_QUIPS, len(_ALL_QUIPS))


QUIPS: list[str] = _shuffle_quips()

PAUSED_QUIP: str = "Gone cold... resume to reheat"

_QUIP_INTERVAL = 8  # seconds per quip


def get_quip(frame: int, *, paused: bool) -> str:
    """Return the current quip with a typewriter reveal effect.

    Characters appear two at a time with a blinking cursor while
    typing. Once fully revealed, the cursor disappears. Quip order
    is shuffled per-session so each launch shows a different sequence.
    """
    if paused:
        return PAUSED_QUIP
    frames_per_quip = _QUIP_INTERVAL * FPS
    quip_idx = (frame // frames_per_quip) % len(QUIPS)
    quip = QUIPS[quip_idx]

    frame_in_quip = frame % frames_per_quip
    chars_to_show = min(len(quip), (frame_in_quip + 1) * 2)

    if chars_to_show < len(quip):
        cursor = "\u2588" if (frame % 6) < 3 else " "
        return quip[:chars_to_show] + cursor
    return quip


# -- Progress bar ------------------------------------------------------------


def _build_progress_bar(
    elapsed: int, total: int, width: int = 20
) -> str:
    """Build a visual progress bar for timed sessions."""
    progress = min(1.0, elapsed / max(1, total))
    filled = int(progress * width)
    bar = "\u2593" * filled + "\u2591" * (width - filled)
    pct = int(progress * 100)
    return f"[cyan]{bar}[/] [dim]{pct}%[/]"


# -- Display assembly --------------------------------------------------------

MODE_DISPLAY: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def format_time(seconds: int) -> str:
    """Format an integer number of seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


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

    Status fields are vertically centered beside the cup art. A progress
    bar appears when a duration is set.
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
    art_lines = steam_lines + cup_lines

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

    art_width = 26
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
