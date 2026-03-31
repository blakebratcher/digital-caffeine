"""Core keep-awake engine for Digital Caffeine."""

from __future__ import annotations

import ctypes
import logging
import threading
from collections.abc import Callable
from datetime import datetime, timedelta

from digital_caffeine.constants import ES_CONTINUOUS, MODE_FLAGS, Mode

logger = logging.getLogger(__name__)


class CaffeineEngine:
    """Prevents Windows from sleeping by periodically asserting execution state flags.

    Supports display-only, system-only, or combined prevention modes. Can run
    indefinitely or auto-stop after a specified duration. Thread-safe and usable
    as a context manager.

    Example usage::

        with CaffeineEngine(mode=Mode.DISPLAY_AND_SYSTEM, duration=3600) as engine:
            # System will stay awake for up to 1 hour
            ...
    """

    def __init__(
        self,
        mode: Mode = Mode.DISPLAY_AND_SYSTEM,
        interval: int = 60,
        duration: int | None = None,
        simulate: bool = False,
    ) -> None:
        """Initialize the engine.

        Args:
            mode: Which sleep prevention mode to use.
            interval: How often (in seconds) to reassert the execution state flags.
            duration: Optional auto-stop after this many seconds. None means indefinite.
            simulate: If True, simulate a tiny mouse movement each cycle to
                register as real user input for apps like Teams and Slack.
        """
        self._mode = mode
        self._interval = interval
        self._duration = duration
        self._simulate = simulate

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        # Start in "not paused" state - the event being set means "not paused"
        self._pause_event.set()

        self._thread: threading.Thread | None = None
        self._start_time: datetime | None = None
        self._active = False
        self._paused = False

        self.on_stop: Callable[[], None] | None = None

    # -- Properties ----------------------------------------------------------

    @property
    def is_active(self) -> bool:
        """Return True if the engine is currently running (started and not stopped)."""
        with self._lock:
            return self._active

    @property
    def is_paused(self) -> bool:
        """Return True if the engine is currently paused."""
        with self._lock:
            return self._paused

    @property
    def mode(self) -> Mode:
        """Return the current sleep prevention mode."""
        return self._mode

    @property
    def simulate(self) -> bool:
        """Return True if input simulation is enabled."""
        return self._simulate

    @property
    def uptime(self) -> timedelta:
        """Return the elapsed time since the engine was started.

        Returns a zero timedelta if the engine has not been started.
        """
        with self._lock:
            if self._start_time is None:
                return timedelta(0)
            return datetime.now() - self._start_time

    @property
    def time_remaining(self) -> timedelta | None:
        """Return the time remaining before auto-stop, or None if no duration is set."""
        with self._lock:
            if self._duration is None or self._start_time is None:
                return None
            elapsed = (datetime.now() - self._start_time).total_seconds()
            remaining = max(0.0, self._duration - elapsed)
            return timedelta(seconds=remaining)

    # -- Core API ------------------------------------------------------------

    def start(self) -> None:
        """Begin keeping the system awake.

        Sets the execution state flags immediately and starts a background
        daemon thread that reasserts them on the configured interval.

        Raises:
            RuntimeError: If the engine is already running.
        """
        with self._lock:
            if self._active:
                raise RuntimeError("CaffeineEngine is already running")

            self._active = True
            self._paused = False
            self._start_time = datetime.now()
            self._stop_event.clear()
            self._pause_event.set()

            self._set_execution_state()
            if self._simulate:
                self._simulate_input()

            self._thread = threading.Thread(
                target=self._worker,
                name="caffeine-worker",
                daemon=True,
            )
            self._thread.start()
            logger.info(
                "CaffeineEngine started (mode=%s, interval=%ds, simulate=%s)",
                self._mode.value,
                self._interval,
                self._simulate,
            )

    def stop(self) -> None:
        """Stop keeping the system awake and restore normal sleep behavior.

        Clears the execution state flags and joins the background thread.
        Safe to call even if the engine is not running.
        """
        with self._lock:
            if not self._active:
                return
            self._active = False
            self._paused = False
            self._stop_event.set()
            # Unblock the worker if it is waiting on the pause event
            self._pause_event.set()

        # Join outside the lock to avoid deadlock with the worker
        if self._thread is not None:
            self._thread.join(timeout=self._interval + 2)
            self._thread = None

        self._clear_execution_state()
        logger.info("CaffeineEngine stopped")

        if self.on_stop is not None:
            try:
                self.on_stop()
            except Exception:
                logger.exception("Error in on_stop callback")

    def pause(self) -> None:
        """Temporarily pause sleep prevention without fully stopping the engine.

        The background thread remains alive but will not reassert flags until
        resumed. The execution state is cleared immediately.
        """
        with self._lock:
            if not self._active or self._paused:
                return
            self._paused = True
            self._pause_event.clear()

        self._clear_execution_state()
        logger.info("CaffeineEngine paused")

    def resume(self) -> None:
        """Resume sleep prevention after a pause.

        Reasserts the execution state flags and unblocks the background thread.
        """
        with self._lock:
            if not self._active or not self._paused:
                return
            self._paused = False
            self._pause_event.set()

        self._set_execution_state()
        logger.info("CaffeineEngine resumed")

    def toggle_pause(self) -> None:
        """Toggle between paused and active states."""
        with self._lock:
            paused = self._paused

        if paused:
            self.resume()
        else:
            self.pause()

    # -- Context manager -----------------------------------------------------

    def __enter__(self) -> CaffeineEngine:
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        self.stop()

    # -- Internal ------------------------------------------------------------

    def _worker(self) -> None:
        """Background thread loop that reasserts flags and checks duration."""
        while not self._stop_event.is_set():
            # Wait for the interval, but wake up early if stop is signalled
            signalled = self._stop_event.wait(timeout=self._interval)
            if signalled:
                break

            # If paused, block here until resumed or stopped
            while not self._pause_event.is_set():
                # Check stop every second while paused
                if self._stop_event.wait(timeout=1.0):
                    return

            # Check duration expiry
            if self._duration is not None and self._start_time is not None:
                elapsed = (datetime.now() - self._start_time).total_seconds()
                if elapsed >= self._duration:
                    logger.info("Duration expired after %s seconds", self._duration)
                    # Call stop outside the worker to allow clean shutdown.
                    # Use a separate thread so we do not join ourselves.
                    threading.Thread(
                        target=self.stop,
                        name="caffeine-duration-stop",
                        daemon=True,
                    ).start()
                    return

            # Reassert the flags
            self._set_execution_state()
            if self._simulate:
                self._simulate_input()

    @staticmethod
    def _simulate_input() -> None:
        """Send a tiny mouse movement to simulate user activity.

        Moves the cursor 1 pixel right then 1 pixel left. This registers
        as real user input to applications like Teams, Slack, and Zoom
        without visibly affecting the cursor position.
        """
        import ctypes.wintypes

        input_mouse = 0
        mouseeventf_move = 0x0001

        class _MouseInput(ctypes.Structure):
            _fields_ = [
                ("dx", ctypes.c_long),
                ("dy", ctypes.c_long),
                ("mouseData", ctypes.wintypes.DWORD),
                ("dwFlags", ctypes.wintypes.DWORD),
                ("time", ctypes.wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
            ]

        class _Input(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.wintypes.DWORD),
                ("mi", _MouseInput),
            ]

        def send_mouse_move(dx: int, dy: int) -> None:
            mi = _MouseInput(
                dx=dx,
                dy=dy,
                mouseData=0,
                dwFlags=mouseeventf_move,
                time=0,
                dwExtraInfo=ctypes.pointer(ctypes.c_ulong(0)),
            )
            inp = _Input(type=input_mouse, mi=mi)
            ctypes.windll.user32.SendInput(  # type: ignore[attr-defined]
                1, ctypes.byref(inp), ctypes.sizeof(inp)
            )

        send_mouse_move(1, 0)
        send_mouse_move(-1, 0)
        logger.debug("Simulated mouse input (1px right, 1px left)")

    def _set_execution_state(self) -> None:
        """Set the Windows execution state flags for the current mode."""
        flags = MODE_FLAGS[self._mode]
        result = ctypes.windll.kernel32.SetThreadExecutionState(flags)  # type: ignore[attr-defined]
        if result == 0:
            logger.warning("SetThreadExecutionState failed (returned 0)")
        else:
            logger.debug("SetThreadExecutionState set to 0x%08X", flags)

    @staticmethod
    def _clear_execution_state() -> None:
        """Clear the execution state flags, restoring normal sleep behavior."""
        result = ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)  # type: ignore[attr-defined]
        if result == 0:
            logger.warning("SetThreadExecutionState clear failed (returned 0)")
        else:
            logger.debug("Execution state cleared (ES_CONTINUOUS only)")
