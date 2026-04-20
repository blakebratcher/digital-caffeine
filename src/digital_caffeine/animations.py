"""Minimal status-line display for the Digital Caffeine CLI.

Public surface:
    run_display(engine, mode, duration_seconds) -> None
    format_elapsed(seconds) -> str
"""

from __future__ import annotations

import os
import random

from digital_caffeine.constants import Mode

FPS = 2

_QUIP_ROTATION_SECONDS = 90
_STARTUP_QUIET_SECONDS = 5

_MODE_PHRASES: dict[Mode, str] = {
    Mode.DISPLAY_ONLY: "keeping display awake",
    Mode.SYSTEM_ONLY: "keeping system awake",
    Mode.DISPLAY_AND_SYSTEM: "keeping display + system awake",
}

_PAUSED_PHRASE = "paused"

QUIPS: list[str] = [
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
    "Schr\u00f6dinger's PC: asleep and awake. JK, it's awake.",
    "The mitochondria is the powerhouse. Caffeine is the keep-awake.",
    "Time is an illusion. Uptime doubly so.",
    "Your PC has transcended the sleep-wake cycle",
    # -- self-referential --
    "This animation runs at 24fps. You're welcome.",
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


def _format_duration(seconds: int) -> str:
    """Format seconds as 'Xh Ym' (no seconds). Clamps negatives to zero."""
    if seconds < 0:
        seconds = 0
    hours, rem = divmod(seconds, 3600)
    minutes = rem // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def _mode_phrase(mode: Mode, paused: bool) -> str:
    """Return the descriptive phrase for the current engine state."""
    if paused:
        return _PAUSED_PHRASE
    return _MODE_PHRASES[mode]


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
