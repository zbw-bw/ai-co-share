"""User idle detection via macOS Quartz CGEventSource.

Reports seconds since last keyboard/mouse event.
"""
from __future__ import annotations

import sys

_IS_MACOS = sys.platform == "darwin"


def _get_idle_seconds_macos() -> float:
    """Return seconds since the last user input event on macOS.

    Returns 0.0 on non-macOS platforms.
    """
    if not _IS_MACOS:
        return 0.0

    import Quartz

    idle_time = Quartz.CGEventSourceSecondsSinceLastEventType(
        Quartz.kCGEventSourceStateCombinedSessionState,
        Quartz.kCGAnyInputEventType,
    )
    return float(idle_time)


def get_idle_seconds() -> float:
    """Return seconds since the last user input event."""
    return _get_idle_seconds_macos()


def is_user_idle(timeout: int = 120) -> bool:
    """Return True if the user has been idle longer than *timeout* seconds."""
    return get_idle_seconds() > timeout
