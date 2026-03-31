"""System tray interface for Digital Caffeine.

Provides a pystray-based tray icon with a right-click context menu for
controlling the keep-awake engine, switching modes, pausing/resuming,
and viewing status information.
"""

from __future__ import annotations

import logging
import threading
from datetime import timedelta

import pystray
from pystray import MenuItem as Item

from digital_caffeine import __version__
from digital_caffeine.constants import Mode
from digital_caffeine.engine import CaffeineEngine
from digital_caffeine.icons import create_active_icon, create_paused_icon, create_stopped_icon

logger = logging.getLogger(__name__)

# Labels used in the mode submenu, mapped to their Mode enum values
_MODE_LABELS: dict[Mode, str] = {
    Mode.DISPLAY_AND_SYSTEM: "Display + System",
    Mode.DISPLAY_ONLY: "Display Only",
    Mode.SYSTEM_ONLY: "System Only",
}


def _format_uptime(td: timedelta) -> str:
    """Format a timedelta as HH:MM:SS."""
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class TrayApp:
    """Manages the system tray icon, menu, and engine lifecycle."""

    def __init__(self, mode: Mode, interval: int, duration: int | None) -> None:
        self._mode = mode
        self._interval = interval
        self._duration = duration

        self._engine = CaffeineEngine(mode=mode, interval=interval, duration=duration)
        self._engine.on_stop = self._on_engine_stop

        self._session_ended = False
        self._update_timer: threading.Timer | None = None
        self._icon: pystray.Icon | None = None

    # -- Menu builders -------------------------------------------------------

    def _build_menu(self) -> pystray.Menu:
        """Build the full right-click context menu."""
        return pystray.Menu(
            Item(
                f"Digital Caffeine v{__version__}",
                action=None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            Item(
                lambda _: self._status_text(),
                action=None,
                enabled=False,
            ),
            Item(
                lambda _: f"Uptime: {_format_uptime(self._engine.uptime)}",
                action=None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            Item(
                "Mode",
                pystray.Menu(
                    Item(
                        _MODE_LABELS[Mode.DISPLAY_AND_SYSTEM],
                        self._make_mode_action(Mode.DISPLAY_AND_SYSTEM),
                        checked=lambda _: self._mode == Mode.DISPLAY_AND_SYSTEM,
                        radio=True,
                    ),
                    Item(
                        _MODE_LABELS[Mode.DISPLAY_ONLY],
                        self._make_mode_action(Mode.DISPLAY_ONLY),
                        checked=lambda _: self._mode == Mode.DISPLAY_ONLY,
                        radio=True,
                    ),
                    Item(
                        _MODE_LABELS[Mode.SYSTEM_ONLY],
                        self._make_mode_action(Mode.SYSTEM_ONLY),
                        checked=lambda _: self._mode == Mode.SYSTEM_ONLY,
                        radio=True,
                    ),
                ),
            ),
            pystray.Menu.SEPARATOR,
            Item(
                lambda _: "Resume" if self._engine.is_paused else "Pause",
                self._on_toggle_pause,
                enabled=lambda _: self._engine.is_active,
            ),
            pystray.Menu.SEPARATOR,
            Item("Quit", self._on_quit),
        )

    def _status_text(self) -> str:
        """Return the current status string for the menu."""
        if self._session_ended:
            return "Status: Session Ended"
        if self._engine.is_paused:
            return "Status: Paused"
        if self._engine.is_active:
            return "Status: Active"
        return "Status: Stopped"

    # -- Mode switching ------------------------------------------------------

    def _make_mode_action(self, new_mode: Mode):
        """Return a callback that switches the engine to the given mode."""

        def _action(icon: pystray.Icon, item: pystray.MenuItem) -> None:
            if new_mode == self._mode:
                return
            logger.info("Switching mode from %s to %s", self._mode.value, new_mode.value)
            self._mode = new_mode

            # Temporarily detach on_stop so the mode-switch stop does not
            # trigger the session-ended logic.
            original_callback = self._engine.on_stop
            self._engine.on_stop = None

            was_paused = self._engine.is_paused
            self._engine.stop()

            self._engine = CaffeineEngine(
                mode=new_mode,
                interval=self._interval,
                duration=self._duration,
            )
            self._engine.on_stop = original_callback
            self._engine.start()

            if was_paused:
                self._engine.pause()
                self._update_icon_for_state()
            else:
                self._update_icon_for_state()

            self._refresh_menu()

        return _action

    # -- Callbacks -----------------------------------------------------------

    def _on_toggle_pause(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Toggle between paused and active states."""
        self._engine.toggle_pause()
        self._update_icon_for_state()
        self._refresh_menu()

    def _on_quit(self, icon: pystray.Icon, item: pystray.MenuItem) -> None:
        """Stop the engine and exit the tray."""
        self._stop_update_timer()
        # Detach callback so stop does not fire session-ended notification
        self._engine.on_stop = None
        self._engine.stop()
        if self._icon is not None:
            self._icon.stop()

    def _on_engine_stop(self) -> None:
        """Called by the engine when the duration expires."""
        logger.info("Engine stopped (duration expired)")
        self._session_ended = True
        self._stop_update_timer()

        if self._icon is not None:
            self._icon.icon = create_stopped_icon()
            self._icon.notify("Session ended", "Digital Caffeine")
            self._refresh_menu()

    # -- Icon management -----------------------------------------------------

    def _update_icon_for_state(self) -> None:
        """Swap the tray icon to match the current engine state."""
        if self._icon is None:
            return

        if self._session_ended:
            self._icon.icon = create_stopped_icon()
        elif self._engine.is_paused:
            self._icon.icon = create_paused_icon()
        else:
            self._icon.icon = create_active_icon()

    # -- Periodic menu refresh -----------------------------------------------

    def _start_update_timer(self) -> None:
        """Schedule a repeating timer to refresh the menu every 5 seconds."""
        self._update_timer = threading.Timer(5.0, self._tick)
        self._update_timer.daemon = True
        self._update_timer.start()

    def _tick(self) -> None:
        """Timer callback - refresh the menu and reschedule."""
        self._refresh_menu()
        # Reschedule unless we have been stopped
        if self._icon is not None and not self._session_ended:
            self._start_update_timer()

    def _stop_update_timer(self) -> None:
        """Cancel the periodic update timer if it is running."""
        if self._update_timer is not None:
            self._update_timer.cancel()
            self._update_timer = None

    def _refresh_menu(self) -> None:
        """Force pystray to re-evaluate the menu (so dynamic labels update)."""
        if self._icon is not None:
            self._icon.update_menu()

    # -- Entry point ---------------------------------------------------------

    def run(self) -> None:
        """Start the engine, create the tray icon, and enter the event loop.

        This method blocks until the user chooses Quit from the tray menu.
        """
        self._engine.start()

        self._icon = pystray.Icon(
            name="digital-caffeine",
            icon=create_active_icon(),
            title="Digital Caffeine",
            menu=self._build_menu(),
        )

        # Start the periodic updater after the icon is created
        self._start_update_timer()

        # icon.run() blocks until icon.stop() is called
        self._icon.run()


def run_tray(mode: Mode, interval: int, duration: int | None) -> None:
    """Main entry point for launching Digital Caffeine in system tray mode.

    Called from the CLI when the user passes the --tray flag. Blocks until the
    user quits via the tray menu.

    Args:
        mode: Which sleep prevention mode to use.
        interval: How often (in seconds) to reassert the execution state flags.
        duration: Optional auto-stop after this many seconds. None means run indefinitely.
    """
    app = TrayApp(mode=mode, interval=interval, duration=duration)
    app.run()
