"""Windows API constants for SetThreadExecutionState and sleep prevention modes."""

from __future__ import annotations

from enum import Enum

# SetThreadExecutionState flags
# See: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
ES_CONTINUOUS = 0x80000000
ES_DISPLAY_REQUIRED = 0x00000002
ES_SYSTEM_REQUIRED = 0x00000001
ES_AWAYMODE_REQUIRED = 0x00000040


class Mode(Enum):
    """Sleep prevention modes.

    DISPLAY_AND_SYSTEM - Prevents both display sleep and system sleep.
    DISPLAY_ONLY - Prevents display sleep only; system may still sleep.
    SYSTEM_ONLY - Prevents system sleep only; display may still turn off.
    """

    DISPLAY_AND_SYSTEM = "display_and_system"
    DISPLAY_ONLY = "display_only"
    SYSTEM_ONLY = "system_only"


# Mapping from Mode to the combined execution state flags.
# ES_CONTINUOUS is always included so the state persists until explicitly cleared.
MODE_FLAGS: dict[Mode, int] = {
    Mode.DISPLAY_AND_SYSTEM: ES_CONTINUOUS | ES_DISPLAY_REQUIRED | ES_SYSTEM_REQUIRED,
    Mode.DISPLAY_ONLY: ES_CONTINUOUS | ES_DISPLAY_REQUIRED,
    Mode.SYSTEM_ONLY: ES_CONTINUOUS | ES_SYSTEM_REQUIRED,
}
