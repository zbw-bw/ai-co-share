from unittest.mock import patch, MagicMock
from PIL import Image
from monitor.screenshot import capture_foreground_window


@patch("monitor.screenshot._get_foreground_window_info")
@patch("monitor.screenshot._capture_window_image")
def test_capture_returns_image_and_title(mock_capture, mock_info):
    mock_info.return_value = ("Test Document - Chrome", "Google Chrome", (100, 100, 800, 600))
    mock_capture.return_value = Image.new("RGB", (700, 500), color="white")

    image, title, process = capture_foreground_window()

    assert image is not None
    assert image.size == (700, 500)
    assert title == "Test Document - Chrome"
    assert process == "Google Chrome"


@patch("monitor.screenshot._get_foreground_window_info")
def test_capture_returns_none_when_no_window(mock_info):
    mock_info.return_value = (None, None, None)

    image, title, process = capture_foreground_window()

    assert image is None
    assert title is None
    assert process is None
