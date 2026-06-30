### Task 10: PyQt6 UI (Main Window + Chat + Status Bar)

**Files:**
- Create: `ui/main_window.py`
- Create: `ui/chat_widget.py`
- Create: `ui/status_bar.py`
- Create: `tests/test_ui.py`

**Interfaces:**
- Consumes: `app.hermes_client.HermesClient` from Task 8
- Produces: `ui.main_window.MainWindow(QMainWindow)` class
- Produces: `ui.chat_widget.ChatWidget(QWidget)` with signal `message_sent(str)` and slot `append_response(str)`
- Produces: `ui.status_bar.StatusBar(QWidget)` with methods `set_hermes_status(bool)`, `set_monitor_status(bool)`

- [ ] **Step 1: Write failing test (smoke test — no display needed)**

```python
# tests/test_ui.py
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


def test_status_bar_creation(qapp):
    from ui.status_bar import StatusBar
    bar = StatusBar()
    bar.set_hermes_status(True)
    bar.set_monitor_status(True)
    bar.set_hermes_status(False)


def test_main_window_creation(qapp):
    from ui.main_window import MainWindow
    window = MainWindow.__new__(MainWindow)
    assert window is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement UI components**

```python
# ui/chat_widget.py
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
)
from PyQt6.QtCore import pyqtSignal, Qt


class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            "QTextEdit { background-color: #f5f5f5; border: 1px solid #ddd; "
            "border-radius: 8px; padding: 8px; font-size: 14px; }"
        )
        layout.addWidget(self._chat_display, stretch=1)

        input_layout = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入消息...")
        self._input_field.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 6px; "
            "padding: 8px; font-size: 14px; }"
        )
        self._input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input_field, stretch=1)

        self._send_button = QPushButton("发送")
        self._send_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self._send_button.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_button)

        layout.addLayout(input_layout)

    def _on_send(self):
        text = self._input_field.text().strip()
        if text:
            self.append_message("user", text)
            self._input_field.clear()
            self.message_sent.emit(text)

    def append_message(self, role: str, content: str):
        if role == "user":
            self._chat_display.append(
                f'<div style="text-align:right; margin:4px 0;">'
                f'<span style="background-color:#DCF8C6; padding:6px 10px; '
                f'border-radius:8px; display:inline-block;">{content}</span></div>'
            )
        else:
            self._chat_display.append(
                f'<div style="text-align:left; margin:4px 0;">'
                f'<span style="background-color:#FFFFFF; padding:6px 10px; '
                f'border-radius:8px; border:1px solid #eee; display:inline-block;">'
                f'{content}</span></div>'
            )

    def set_input_enabled(self, enabled: bool):
        self._input_field.setEnabled(enabled)
        self._send_button.setEnabled(enabled)
```

```python
# ui/status_bar.py
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class StatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        self._hermes_label = QLabel()
        self._monitor_label = QLabel()

        layout.addWidget(self._monitor_label)
        layout.addStretch()
        layout.addWidget(self._hermes_label)

        self.set_hermes_status(False)
        self.set_monitor_status(False)

    def set_hermes_status(self, connected: bool):
        if connected:
            self._hermes_label.setText("Agent: 已连接")
            self._hermes_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self._hermes_label.setText("Agent: 未连接")
            self._hermes_label.setStyleSheet("color: red; font-size: 12px;")

    def set_monitor_status(self, running: bool):
        if running:
            self._monitor_label.setText("监控: 运行中")
            self._monitor_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self._monitor_label.setText("监控: 已停止")
            self._monitor_label.setStyleSheet("color: gray; font-size: 12px;")
```

```python
# ui/main_window.py
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from ui.chat_widget import ChatWidget
from ui.status_bar import StatusBar


class MainWindow(QMainWindow):
    def __init__(
        self,
        on_message_sent=None,
        width: int = 400,
        height: int = 600,
    ):
        super().__init__()
        self.setWindowTitle("逗叽脑袋 - 桌面宠物 Agent")
        self.setFixedSize(width, height)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget, stretch=1)

        self.status_bar = StatusBar()
        layout.addWidget(self.status_bar)

        if on_message_sent:
            self.chat_widget.message_sent.connect(on_message_sent)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py -v`
Expected: All 3 tests PASS (may need `QT_QPA_PLATFORM=offscreen` on headless systems)

- [ ] **Step 5: Commit**

```bash
git add ui/ tests/test_ui.py
git commit -m "feat: PyQt6 UI with chat widget and status bar"
```

---

