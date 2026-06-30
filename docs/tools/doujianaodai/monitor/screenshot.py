"""Foreground window screenshot capture using macOS Quartz API.

Requires screen recording permission in System Settings > Privacy & Security.
"""
from __future__ import annotations

import sys
from typing import Optional

from PIL import Image

_IS_MACOS = sys.platform == "darwin"


def _get_foreground_window_info() -> tuple[Optional[str], Optional[str], Optional[tuple]]:
    """Return (window_title, app_name, (x, y, w, h)) for the frontmost window.

    Returns (None, None, None) if no suitable window is found or not on macOS.
    """
    if not _IS_MACOS:
        return None, None, None

    import Quartz
    import AppKit

    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if not app:
        return None, None, None

    app_name = app.localizedName() or "unknown"
    pid = app.processIdentifier()

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )

    for window in window_list:
        if window.get(Quartz.kCGWindowOwnerPID) == pid:
            title = window.get(Quartz.kCGWindowName, "")
            if not title:
                continue
            bounds = window.get(Quartz.kCGWindowBounds, {})
            x = int(bounds.get("X", 0))
            y = int(bounds.get("Y", 0))
            w = int(bounds.get("Width", 0))
            h = int(bounds.get("Height", 0))
            if w > 0 and h > 0:
                return title, app_name, (x, y, w, h)

    return None, None, None


def _capture_window_image(rect: tuple) -> Optional[Image.Image]:
    """Capture a screenshot of the given screen rectangle.

    Returns a PIL RGB Image, or None on failure.
    """
    if not _IS_MACOS:
        return None

    import Quartz

    x, y, w, h = rect
    cg_rect = Quartz.CGRectMake(x, y, w, h)
    cg_image = Quartz.CGWindowListCreateImage(
        cg_rect,
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault,
    )

    if cg_image is None:
        return None

    width = Quartz.CGImageGetWidth(cg_image)
    height = Quartz.CGImageGetHeight(cg_image)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)
    data_provider = Quartz.CGImageGetDataProvider(cg_image)
    data = Quartz.CGDataProviderCopyData(data_provider)

    image = Image.frombuffer(
        "RGBA", (width, height), data, "raw", "BGRA", bytes_per_row, 1,
    )
    return image.convert("RGB")


def capture_foreground_window() -> tuple[Optional[Image.Image], Optional[str], Optional[str]]:
    """Capture a screenshot of the current foreground window.

    Returns:
        (image, window_title, process_name) — all None when no window is found.
    """
    title, app_name, rect = _get_foreground_window_info()
    if title is None or rect is None:
        return None, None, None
    image = _capture_window_image(rect)
    return image, title, app_name
