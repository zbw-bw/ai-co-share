# tests/test_ui.py — full rewrite
import sys
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_chat_widget_creation(qapp):
    from ui.chat_widget import ChatWidget
    widget = ChatWidget()
    assert widget is not None
    widget.append_message("user", "Hello")
    widget.append_message("assistant", "Hi there")


def test_chat_widget_stream_events(qapp):
    from ui.chat_widget import ChatWidget
    widget = ChatWidget()
    widget.handle_stream_event({"event_type": "status", "content": "已连接 claude-sonnet", "metadata": {}})
    widget.handle_stream_event({"event_type": "thinking", "content": "Let me check...", "metadata": {}})
    widget.handle_stream_event({"event_type": "tool_use", "content": "read_activity_index", "metadata": {"input": {"date": "today"}}})
    widget.handle_stream_event({"event_type": "tool_result", "content": "3 activities", "metadata": {}})
    widget.handle_stream_event({"event_type": "text", "content": "你今天做了三件事", "metadata": {}})
    widget.handle_stream_event({"event_type": "done", "content": "", "metadata": {}})


def test_chat_widget_clear(qapp):
    from ui.chat_widget import ChatWidget
    widget = ChatWidget()
    widget.append_message("user", "Hello")
    widget.clear_chat()
    assert widget._chat_display.toPlainText() == ""


def test_overview_widget_creation(qapp):
    from ui.overview_widget import OverviewWidget
    widget = OverviewWidget()
    assert widget is not None


def test_activity_log_widget_creation(qapp):
    from ui.activity_log_widget import ActivityLogWidget
    widget = ActivityLogWidget()
    assert widget is not None


def test_settings_widget_creation(qapp):
    from ui.settings_widget import SettingsWidget
    config = {
        "monitor": {"interval_seconds": 15, "engage_threshold": 5},
        "screenshots": {"retention_days": 7},
        "ocr": {"retention_days": 7},
        "logs": {"retention_days": 30},
        "llm": {"local": {"model": "qwen3:8b", "base_url": "http://localhost:11434"}},
    }
    widget = SettingsWidget(config=config, config_path="/tmp/test_config.yaml", on_config_changed=lambda c: None)
    assert widget is not None


def test_tray_app_creation(qapp):
    from ui.tray_app import TrayApp
    config = {
        "ui": {"window_width": 420, "window_height": 520},
        "monitor": {"interval_seconds": 15, "engage_threshold": 5},
        "screenshots": {"retention_days": 7},
        "ocr": {"retention_days": 7},
        "logs": {"retention_days": 30},
        "llm": {"local": {"model": "qwen3:8b", "base_url": "http://localhost:11434"}},
    }
    tray = TrayApp(config=config, config_path="/tmp/test.yaml", on_message_sent=lambda t: None)
    assert tray.tray_icon is not None
    assert tray.panel is not None
    tray.update_monitor_status(True)
    tray.update_agent_status(True)
