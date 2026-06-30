### Task 5: Rewire PetApp — TrayApp + Streaming ChatWorker

**Files:**
- Modify: `app/main.py`
- Test: `tests/test_app_main.py` (modify)

**Interfaces:**
- Consumes: `TrayApp` from `ui/tray_app.py` (Task 4), `ClaudeClient.send_message_stream` (Task 2), `run_preflight` from `app/preflight.py` (Task 3), `StreamEvent` from `app/stream_parser.py` (Task 1)
- Produces: `PetApp` class (same name, updated internals), `main()` entry point. `ChatWorker` now yields stream events via `stream_event = pyqtSignal(dict)` instead of `response_ready = pyqtSignal(str)`.

- [ ] **Step 1: Write the failing tests**

Rewrite `tests/test_app_main.py`:

```python
# tests/test_app_main.py
import sys
import pytest
from unittest.mock import patch, MagicMock


def test_pet_app_construction():
    with patch("app.main.load_config") as mock_load:
        mock_load.return_value = {
            "monitor": {"enabled": True, "interval_seconds": 15, "idle_timeout_seconds": 120, "engage_threshold": 5},
            "screenshots": {"quality": 75, "cleanup_similarity": 0.9, "retention_days": 7},
            "ocr": {"engine": "paddleocr", "lang": "ch", "retention_days": 7},
            "llm": {"local": {"provider": "ollama", "model": "qwen3:8b", "base_url": "http://localhost:11434"}},
            "logs": {"retention_days": 30},
            "memory": {"base_dir": "~/.pet-memory", "embedding_model": "bge-small-zh"},
            "ui": {"window_width": 420, "window_height": 520},
        }
        with patch("app.main.ScreenMonitor"):
            with patch("app.main.SummaryGenerator"):
                from app.main import PetApp
                app = PetApp.__new__(PetApp)
                assert app is not None


def test_chat_worker_emits_stream_events():
    from app.main import ChatWorker
    from app.stream_parser import StreamEvent

    mock_client = MagicMock()
    events = [
        StreamEvent("text", "hello", {}),
        StreamEvent("done", "", {"session_id": "s1"}),
    ]
    mock_client.send_message_stream.return_value = iter(events)

    worker = ChatWorker(mock_client, "hi")
    received = []
    worker.stream_event.connect(lambda d: received.append(d))
    worker.run()

    assert len(received) == 2
    assert received[0]["event_type"] == "text"
    assert received[1]["event_type"] == "done"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_app_main.py -v`
Expected: FAIL — `ChatWorker` has no `stream_event` signal

- [ ] **Step 3: Rewrite app/main.py**

```python
# app/main.py
"""Application entry point — orchestrates monitor, Claude Code bridge, and UI."""
from __future__ import annotations

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

from app.config import load_config
from app.claude_client import ClaudeClient
from monitor.screen_monitor import ScreenMonitor
from memory.summary_generator import SummaryGenerator
from logs.pet_logger import ChatLogger, StatsCollector
from ui.tray_app import TrayApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

MEMORY_DIR = os.path.expanduser("~/.pet-memory")


class ChatWorker(QThread):
    stream_event = pyqtSignal(dict)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, client: ClaudeClient, message: str):
        super().__init__()
        self._client = client
        self._message = message

    def run(self):
        try:
            for event in self._client.send_message_stream(self._message):
                self.stream_event.emit(event.to_dict())
        except Exception as e:
            self.error_occurred.emit(f"对话出错: {e}")
        self.finished.emit()


class PetApp:
    def __init__(self, config: dict | None = None, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        self._config_path = config_path

        if config is not None:
            self._config = config
        else:
            self._config = load_config(config_path)

        os.makedirs(MEMORY_DIR, exist_ok=True)

        self._stats = StatsCollector(MEMORY_DIR)
        self._chat_logger = ChatLogger(MEMORY_DIR)

        self._client = ClaudeClient(
            chat_logger=self._chat_logger,
            stats_collector=self._stats,
        )
        self._monitor = ScreenMonitor(
            base_dir=MEMORY_DIR,
            interval=self._config["monitor"]["interval_seconds"],
            idle_timeout=self._config["monitor"]["idle_timeout_seconds"],
            engage_threshold=self._config["monitor"].get("engage_threshold", 5),
            screenshot_quality=self._config["screenshots"]["quality"],
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
            stats_collector=self._stats,
        )
        self._summary_gen = SummaryGenerator(
            base_dir=MEMORY_DIR,
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._tray: TrayApp | None = None
        self._health_timer: QTimer | None = None
        self._chat_worker: ChatWorker | None = None

    def run(self):
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        self._tray = TrayApp(
            config=self._config,
            config_path=self._config_path,
            on_message_sent=self._on_user_message,
        )

        self._start_services()

        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(30000)

        exit_code = app.exec()
        self._shutdown()
        sys.exit(exit_code)

    def _start_services(self):
        if self._tray:
            self._tray.chat_widget.append_message("system", "逗叽脑袋已启动，对话将通过 Claude Code 处理。")

        if self._config["monitor"]["enabled"]:
            self._monitor.start()
            if self._tray:
                self._tray.update_monitor_status(True)

        self._summary_gen.check_and_generate_pending()

        if self._tray:
            self._tray.activity_log_widget.set_base_dir(MEMORY_DIR)
            self._tray.overview_widget.refresh(
                stats_dir=str(os.path.join(MEMORY_DIR, "logs", "stats")),
                index_dir=str(os.path.join(MEMORY_DIR, "index")),
            )

    def _on_user_message(self, text: str):
        if self._tray:
            self._tray.chat_widget.set_input_enabled(False)

        self._chat_worker = ChatWorker(self._client, text)
        self._chat_worker.stream_event.connect(self._on_stream_event)
        self._chat_worker.error_occurred.connect(self._on_error)
        self._chat_worker.finished.connect(self._on_chat_finished)
        self._chat_worker.start()

    def _on_stream_event(self, event: dict):
        if self._tray:
            self._tray.chat_widget.handle_stream_event(event)

    def _on_chat_finished(self):
        if self._tray:
            self._tray.chat_widget.set_input_enabled(True)
            self._tray.overview_widget.refresh(
                stats_dir=str(os.path.join(MEMORY_DIR, "logs", "stats")),
                index_dir=str(os.path.join(MEMORY_DIR, "index")),
            )

    def _on_error(self, error: str):
        if self._tray:
            self._tray.chat_widget.append_message("system", error)
            self._tray.chat_widget.set_input_enabled(True)

    def _check_health(self):
        monitor_ok = self._monitor.is_running()
        if self._tray:
            self._tray.update_monitor_status(monitor_ok)

    def _shutdown(self):
        logger.info("Shutting down...")
        self._monitor.stop()

        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")

        self._stats.flush(today)
        self._summary_gen.generate_daily(today)

        from memory.screenshot_cleaner import cleanup_similar, cleanup_expired, cleanup_logs_expired
        from monitor.ocr_store import cleanup_ocr_expired

        cleanup_similar(MEMORY_DIR, today, self._config["screenshots"]["cleanup_similarity"])
        cleanup_expired(MEMORY_DIR, self._config["screenshots"]["retention_days"])
        cleanup_ocr_expired(MEMORY_DIR, self._config["ocr"].get("retention_days", 7))
        cleanup_logs_expired(MEMORY_DIR, self._config.get("logs", {}).get("retention_days", 30))

        logger.info("Shutdown complete")


def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    try:
        from app.preflight import run_preflight
        config = run_preflight(config_path)
    except SystemExit:
        return
    pet = PetApp(config=config, config_path=config_path)
    pet.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_app_main.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run all tests**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_app_main.py
git commit -m "feat: rewire PetApp to use TrayApp with streaming ChatWorker"
```

---
