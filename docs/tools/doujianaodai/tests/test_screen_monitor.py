# tests/test_screen_monitor.py
from unittest.mock import patch, MagicMock
from monitor.screen_monitor import ScreenMonitor


def test_monitor_start_stop(tmp_path):
    monitor = ScreenMonitor(base_dir=str(tmp_path), interval=0.1, engage_threshold=2)
    monitor.start()
    assert monitor.is_running()
    monitor.stop()
    assert not monitor.is_running()


@patch("monitor.screen_monitor.capture_foreground_window")
@patch("monitor.screen_monitor.is_user_idle", return_value=False)
@patch("monitor.screen_monitor.recognize_text_with_skip", return_value=("test ocr content " * 10, False))
def test_tick_saves_screenshot_and_ocr(mock_ocr, mock_idle, mock_capture, tmp_path):
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    mock_capture.return_value = (img, "Test Title", "Google Chrome")

    monitor = ScreenMonitor(base_dir=str(tmp_path), interval=60, engage_threshold=2)
    monitor._tick()

    screenshots = list((tmp_path / "screenshots").rglob("*.jpg"))
    assert len(screenshots) == 1
    ocr_files = list((tmp_path / "ocr").rglob("*.txt"))
    assert len(ocr_files) == 1
