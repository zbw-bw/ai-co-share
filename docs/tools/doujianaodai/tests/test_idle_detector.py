from unittest.mock import patch
from monitor.idle_detector import get_idle_seconds, is_user_idle


@patch("monitor.idle_detector._get_idle_seconds_macos")
def test_get_idle_seconds(mock_idle):
    mock_idle.return_value = 3.0
    assert get_idle_seconds() == 3.0


@patch("monitor.idle_detector.get_idle_seconds")
def test_is_user_idle_true(mock_idle):
    mock_idle.return_value = 150.0
    assert is_user_idle(120) is True


@patch("monitor.idle_detector.get_idle_seconds")
def test_is_user_idle_false(mock_idle):
    mock_idle.return_value = 30.0
    assert is_user_idle(120) is False
