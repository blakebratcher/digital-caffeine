"""Comprehensive tests for the CaffeineEngine keep-awake engine."""

from __future__ import annotations

import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from digital_caffeine.constants import ES_CONTINUOUS, MODE_FLAGS, Mode
from digital_caffeine.engine import CaffeineEngine

# Target path for patching the Windows API call used inside the engine module.
_STE_PATH = "digital_caffeine.engine.ctypes.windll.kernel32.SetThreadExecutionState"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_set_execution_state():
    """Patch SetThreadExecutionState for every test so the Windows API is never called.

    Yields a MagicMock whose return value is 1 (success).
    """
    with patch(_STE_PATH, return_value=1) as mock:
        yield mock


@pytest.fixture()
def mock_ste(_mock_set_execution_state):
    """Expose the SetThreadExecutionState mock to tests that need to inspect calls."""
    return _mock_set_execution_state


@pytest.fixture()
def engine():
    """Create a default CaffeineEngine and ensure it is stopped after the test."""
    eng = CaffeineEngine()
    yield eng
    # Safety net - stop the engine if the test forgot to
    eng.stop()


@pytest.fixture()
def engine_with_duration():
    """Create a CaffeineEngine with a short duration for time-remaining tests."""
    eng = CaffeineEngine(duration=10)
    yield eng
    eng.stop()


# ---------------------------------------------------------------------------
# Tests - Start / Stop
# ---------------------------------------------------------------------------


class TestStartStop:
    """Tests for starting and stopping the engine."""

    def test_engine_starts_and_stops(self, engine: CaffeineEngine) -> None:
        """Verify is_active flips to True on start and back to False on stop."""
        assert engine.is_active is False

        engine.start()
        assert engine.is_active is True

        engine.stop()
        assert engine.is_active is False

    def test_engine_double_start_raises(self, engine: CaffeineEngine) -> None:
        """Starting the engine twice without stopping should raise RuntimeError."""
        engine.start()

        with pytest.raises(RuntimeError, match="already running"):
            engine.start()

        engine.stop()

    def test_engine_stop_when_not_running(self, engine: CaffeineEngine) -> None:
        """Calling stop() on an engine that was never started should not raise."""
        # Should complete without error
        engine.stop()
        assert engine.is_active is False


# ---------------------------------------------------------------------------
# Tests - Pause / Resume
# ---------------------------------------------------------------------------


class TestPauseResume:
    """Tests for pausing and resuming the engine."""

    def test_engine_pause_resume(self, engine: CaffeineEngine) -> None:
        """Verify is_paused toggles correctly through a pause/resume cycle."""
        engine.start()
        assert engine.is_paused is False

        engine.pause()
        assert engine.is_paused is True

        engine.resume()
        assert engine.is_paused is False

        engine.stop()

    def test_engine_toggle_pause(self, engine: CaffeineEngine) -> None:
        """toggle_pause() should alternate between paused and active states."""
        engine.start()
        assert engine.is_paused is False

        engine.toggle_pause()
        assert engine.is_paused is True

        engine.toggle_pause()
        assert engine.is_paused is False

        engine.stop()


# ---------------------------------------------------------------------------
# Tests - Uptime
# ---------------------------------------------------------------------------


class TestUptime:
    """Tests for the uptime property."""

    def test_engine_uptime_increases(self, engine: CaffeineEngine) -> None:
        """uptime should grow after the engine is started."""
        assert engine.uptime == timedelta(0)

        engine.start()
        time.sleep(0.05)
        uptime_snapshot = engine.uptime
        assert uptime_snapshot > timedelta(0)

        # A second reading should be even larger
        time.sleep(0.05)
        assert engine.uptime > uptime_snapshot

        engine.stop()


# ---------------------------------------------------------------------------
# Tests - Time Remaining
# ---------------------------------------------------------------------------


class TestTimeRemaining:
    """Tests for the time_remaining property."""

    def test_engine_time_remaining_none_when_no_duration(
        self, engine: CaffeineEngine
    ) -> None:
        """time_remaining is None when no duration was configured."""
        engine.start()
        assert engine.time_remaining is None
        engine.stop()

    def test_engine_time_remaining_decreases(
        self, engine_with_duration: CaffeineEngine
    ) -> None:
        """time_remaining should decrease over time when a duration is set."""
        engine_with_duration.start()

        first = engine_with_duration.time_remaining
        assert first is not None
        assert first <= timedelta(seconds=10)

        time.sleep(0.1)

        second = engine_with_duration.time_remaining
        assert second is not None
        assert second < first

        engine_with_duration.stop()


# ---------------------------------------------------------------------------
# Tests - Context Manager
# ---------------------------------------------------------------------------


class TestContextManager:
    """Tests for context manager (with-statement) support."""

    def test_engine_context_manager(self) -> None:
        """Using CaffeineEngine as a context manager should start and stop it."""
        eng = CaffeineEngine()
        assert eng.is_active is False

        with eng:
            assert eng.is_active is True

        assert eng.is_active is False


# ---------------------------------------------------------------------------
# Tests - Mode Property
# ---------------------------------------------------------------------------


class TestModeProperty:
    """Tests for the mode property."""

    def test_engine_mode_property(self) -> None:
        """mode property should return the Mode that was passed to the constructor."""
        for m in Mode:
            eng = CaffeineEngine(mode=m)
            assert eng.mode is m
            # No need to start/stop - mode is available immediately


# ---------------------------------------------------------------------------
# Tests - on_stop Callback
# ---------------------------------------------------------------------------


class TestOnStopCallback:
    """Tests for the on_stop callback."""

    def test_engine_on_stop_callback(self, engine: CaffeineEngine) -> None:
        """The on_stop callback should fire when the engine stops."""
        callback = MagicMock()
        engine.on_stop = callback

        engine.start()
        engine.stop()

        callback.assert_called_once()

    def test_engine_on_stop_callback_not_called_when_not_running(
        self, engine: CaffeineEngine
    ) -> None:
        """The on_stop callback should not fire if the engine was never started."""
        callback = MagicMock()
        engine.on_stop = callback

        engine.stop()

        callback.assert_not_called()


# ---------------------------------------------------------------------------
# Tests - SetThreadExecutionState Calls
# ---------------------------------------------------------------------------


class TestExecutionStateCalls:
    """Tests that verify the mock SetThreadExecutionState is called correctly."""

    def test_engine_sets_execution_state(self, mock_ste: MagicMock) -> None:
        """Starting the engine should call SetThreadExecutionState with the correct flags."""
        for m in Mode:
            mock_ste.reset_mock()

            eng = CaffeineEngine(mode=m)
            eng.start()

            expected_flags = MODE_FLAGS[m]
            mock_ste.assert_any_call(expected_flags)

            eng.stop()

    def test_engine_clears_state_on_stop(self, mock_ste: MagicMock) -> None:
        """Stopping the engine should call SetThreadExecutionState with ES_CONTINUOUS only."""
        eng = CaffeineEngine(mode=Mode.DISPLAY_AND_SYSTEM)
        eng.start()

        mock_ste.reset_mock()
        eng.stop()

        # After stop, the last call should clear state with ES_CONTINUOUS
        mock_ste.assert_called_with(ES_CONTINUOUS)

    def test_engine_clears_state_on_pause(self, mock_ste: MagicMock) -> None:
        """Pausing the engine should clear the execution state flags."""
        eng = CaffeineEngine(mode=Mode.DISPLAY_AND_SYSTEM)
        eng.start()

        mock_ste.reset_mock()
        eng.pause()

        mock_ste.assert_called_with(ES_CONTINUOUS)
        eng.stop()

    def test_engine_restores_state_on_resume(self, mock_ste: MagicMock) -> None:
        """Resuming the engine should reassert the mode-specific flags."""
        mode = Mode.DISPLAY_AND_SYSTEM
        eng = CaffeineEngine(mode=mode)
        eng.start()
        eng.pause()

        mock_ste.reset_mock()
        eng.resume()

        expected_flags = MODE_FLAGS[mode]
        mock_ste.assert_called_with(expected_flags)
        eng.stop()


# ---------------------------------------------------------------------------
# Tests - Simulate Property
# ---------------------------------------------------------------------------


class TestSimulate:
    """Tests for the simulate input feature."""

    def test_simulate_defaults_false(self) -> None:
        """simulate defaults to False."""
        eng = CaffeineEngine()
        assert eng.simulate is False
        eng.stop()

    def test_simulate_property(self) -> None:
        """simulate property returns the value passed to the constructor."""
        eng = CaffeineEngine(simulate=True)
        assert eng.simulate is True
        eng.stop()

    @patch(
        "digital_caffeine.engine.CaffeineEngine._simulate_input"
    )
    def test_simulate_calls_simulate_input(self, mock_sim: MagicMock) -> None:
        """When simulate is True, _simulate_input should be called on start."""
        eng = CaffeineEngine(simulate=True)
        eng.start()

        mock_sim.assert_called()
        eng.stop()

    @patch(
        "digital_caffeine.engine.CaffeineEngine._simulate_input"
    )
    def test_no_simulate_does_not_call(self, mock_sim: MagicMock) -> None:
        """When simulate is False, _simulate_input should not be called."""
        eng = CaffeineEngine(simulate=False)
        eng.start()
        time.sleep(0.05)

        mock_sim.assert_not_called()
        eng.stop()
