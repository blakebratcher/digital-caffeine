"""Click CLI interface for Digital Caffeine - a Windows keep-awake utility."""

from __future__ import annotations

import re
import sys
import time

import click
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

from digital_caffeine import __version__
from digital_caffeine.animations import build_animated_display
from digital_caffeine.config import get_config_path, load_config
from digital_caffeine.constants import Mode

console = Console()

# Maps CLI mode names to the Mode enum values
MODE_MAP: dict[str, Mode] = {
    "all": Mode.DISPLAY_AND_SYSTEM,
    "display": Mode.DISPLAY_ONLY,
    "system": Mode.SYSTEM_ONLY,
}

# Reverse map for display purposes
MODE_DISPLAY: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def parse_duration(s: str) -> int:
    """Parse a human-friendly duration string into total seconds.

    Supported formats:
        "30s"     -> 30 seconds
        "30m"     -> 30 minutes
        "2h"      -> 2 hours
        "1h30m"   -> 1 hour 30 minutes
        "1h30m15s"-> 1 hour 30 minutes 15 seconds

    Args:
        s: Duration string to parse.

    Returns:
        Total number of seconds.

    Raises:
        click.BadParameter: If the string cannot be parsed.
    """
    s = s.strip().lower()

    pattern = r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$"
    match = re.fullmatch(pattern, s)

    if not match or not any(match.groups()):
        raise click.BadParameter(
            f"Invalid duration '{s}'. Use formats like 30s, 30m, 2h, 1h30m, or 1h30m15s."
        )

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total = hours * 3600 + minutes * 60 + seconds
    if total <= 0:
        raise click.BadParameter("Duration must be greater than zero.")

    return total


def format_time(seconds: int) -> str:
    """Format an integer number of seconds as HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


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


@click.group()
def cli() -> None:
    """Digital Caffeine - Keep your Windows machine awake.

    Prevent your display and system from sleeping. Run 'caffeine start' to begin,
    or use 'caffeine config' to manage settings.
    """


@cli.command()
@click.option(
    "--mode",
    "-m",
    "mode_name",
    type=click.Choice(["all", "display", "system"], case_sensitive=False),
    default=None,
    help='Prevention mode: "all", "display", or "system". Defaults to config or "all".',
)
@click.option(
    "--interval",
    "-i",
    type=int,
    default=None,
    help="Refresh interval in seconds. Defaults to config value or 60.",
)
@click.option(
    "--duration",
    "-d",
    "duration_str",
    type=str,
    default=None,
    help="Run for a limited time (e.g. 30m, 2h, 1h30m). Omit for indefinite.",
)
@click.option(
    "--tray",
    "-t",
    is_flag=True,
    default=False,
    help="Launch in system tray mode instead of the terminal UI.",
)
@click.option(
    "--simulate",
    "-s",
    is_flag=True,
    default=None,
    help="Simulate mouse input to keep apps like Teams active. Off by default.",
)
def start(
    mode_name: str | None,
    interval: int | None,
    duration_str: str | None,
    tray: bool,
    simulate: bool | None,
) -> None:
    """Start keeping your machine awake.

    By default, runs an interactive terminal UI that shows live status. Use --tray
    to launch the system tray icon instead.
    """
    # Load config and apply defaults
    config = load_config()

    if mode_name is None:
        mode_name = config.get("mode", "all")
    if interval is None:
        interval = config.get("interval", 60)

    mode = MODE_MAP[mode_name]

    duration_seconds: int | None = None
    if duration_str is not None:
        duration_seconds = parse_duration(duration_str)
    elif config.get("duration") is not None:
        duration_seconds = parse_duration(config["duration"])

    if simulate is None:
        simulate = config.get("simulate", False)

    # System tray mode
    if tray:
        console.print("[cyan]Launching system tray mode...[/cyan]")
        try:
            from digital_caffeine.tray import run_tray
        except ImportError:
            console.print(
                "[red]Error:[/red] Tray dependencies are not installed. "
                "Install the tray extras to use this feature."
            )
            sys.exit(1)
        run_tray(mode=mode, interval=interval, duration=duration_seconds, simulate=simulate)
        return

    # CLI live display mode
    from digital_caffeine.engine import CaffeineEngine

    engine = CaffeineEngine(mode=mode, interval=interval, simulate=simulate)
    engine.start()

    start_time = time.monotonic()
    console.print(
        f"[green]Digital Caffeine started[/green] - mode={MODE_DISPLAY[mode]}, interval={interval}s"
    )

    try:
        with Live(
            build_display(
                mode=mode,
                uptime_seconds=0,
                duration_seconds=duration_seconds,
                interval=interval,
                paused=False,
                simulate=simulate,
            ),
            console=console,
            refresh_per_second=1,
            transient=False,
        ) as live:
            while True:
                elapsed = int(time.monotonic() - start_time)

                # If a duration was set and we've exceeded it, stop automatically
                if duration_seconds is not None and elapsed >= duration_seconds:
                    break

                live.update(
                    build_display(
                        mode=mode,
                        uptime_seconds=elapsed,
                        duration_seconds=duration_seconds,
                        interval=interval,
                        paused=False,
                        simulate=simulate,
                    )
                )
                time.sleep(1)
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


@cli.command()
@click.option("--show", is_flag=True, default=False, help="Print the current config file contents.")
@click.option("--init", is_flag=True, default=False, help="Create a default config file.")
@click.option("--path", is_flag=True, default=False, help="Print the config file path.")
def config(show: bool, init: bool, path: bool) -> None:
    """View or manage the Digital Caffeine configuration file."""
    config_path = get_config_path()

    if path:
        console.print(str(config_path))
        return

    if show:
        if config_path.exists():
            contents = config_path.read_text(encoding="utf-8")
            console.print(f"[bold]Config file:[/bold] {config_path}\n")
            console.print(contents)
        else:
            console.print("[yellow]No config file found.[/yellow]")
            console.print(f"Expected location: {config_path}")
            console.print("Run 'caffeine config --init' to create one.")
        return

    if init:
        if config_path.exists():
            if not click.confirm(
                f"Config file already exists at {config_path}. Overwrite?"
            ):
                console.print("[yellow]Aborted.[/yellow]")
                return

        from digital_caffeine.config import create_default_config

        created_path = create_default_config()
        console.print(f"[green]Config file created at:[/green] {created_path}")
        return

    # No flag provided - show help
    console.print("Use --show, --init, or --path. Run 'caffeine config --help' for details.")


@cli.command()
def version() -> None:
    """Print the Digital Caffeine version."""
    console.print(f"Digital Caffeine v{__version__}")
