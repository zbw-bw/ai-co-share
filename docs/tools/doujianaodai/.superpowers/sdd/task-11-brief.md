### Task 11: Application Entry Point (Orchestration)

**Files:**
- Create: `app/main.py`
- Modify: `tests/test_config.py` — add `_config_instance` reset in setup

**Interfaces:**
- Consumes: All previous tasks
- Produces: `app.main.main() -> None` — entry point that starts the application

- [ ] **Step 1: Write failing test**

```python
# tests/test_app_main.py
from unittest.mock import patch, MagicMock


@patch("app.main.QApplication")
@patch("app.main.HermesLauncher")
@patch("app.main.ScreenMonitor")
@patch("app.main.MainWindow")
@patch("app.main.SummaryGenerator")
def test_app_startup_sequence(
    mock_summary_gen, mock_window, mock_monitor, mock_launcher, mock_qapp,
):
    mock_launcher_instance = MagicMock()
    mock_launcher_instance.is_installed.return_value = True
    mock_launcher_instance.start.return_value = True
    mock_launcher_instance.is_healthy.return_value = True
    mock_launcher.return_value = mock_launcher_instance

    mock_monitor_instance = MagicMock()
    mock_monitor.return_value = mock_monitor_instance

    mock_window_instance = MagicMock()
    mock_window.return_value = mock_window_instance

    mock_qapp_instance = MagicMock()
    mock_qapp.return_value = mock_qapp_instance
    mock_qapp_instance.exec.return_value = 0

    from app.main import PetApp
    app = PetApp.__new__(PetApp)
    app._config = {
        "monitor": {"enabled": True, "interval_seconds": 30, "idle_timeout_seconds": 120,
                     "confirm_count": 2},
        "screenshots": {"quality": 75},
        "memory": {"base_dir": "/tmp/test-pet-memory"},
        "llm": {"local": {"base_url": "http://localhost:11434", "model": "qwen2.5:7b"}},
        "ui": {"window_width": 400, "window_height": 600},
    }
    app._launcher = mock_launcher_instance
    app._monitor = mock_monitor_instance
    app._summary_gen = MagicMock()

    app._start_services()

    mock_launcher_instance.start.assert_called_once()
    mock_monitor_instance.start.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_app_main.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement application entry point**

```python
# app/main.py
from __future__ import annotations

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from app.config import load_config, get_config
from app.hermes_launcher import HermesLauncher
from app.hermes_client import HermesClient
from monitor.screen_monitor import ScreenMonitor
from memory.summary_generator import SummaryGenerator
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


class PetApp:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        self._config = load_config(config_path)

        memory_dir = self._config["memory"]["base_dir"]
        os.makedirs(memory_dir, exist_ok=True)

        self._launcher = HermesLauncher()
        self._client = HermesClient()
        self._monitor = ScreenMonitor(
            base_dir=memory_dir,
            interval=self._config["monitor"]["interval_seconds"],
            idle_timeout=self._config["monitor"]["idle_timeout_seconds"],
            confirm_count=self._config["monitor"]["confirm_count"],
            screenshot_quality=self._config["screenshots"]["quality"],
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._summary_gen = SummaryGenerator(
            base_dir=memory_dir,
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._window: MainWindow | None = None
        self._health_timer: QTimer | None = None

    def run(self):
        app = QApplication(sys.argv)

        self._window = MainWindow(
            on_message_sent=self._on_user_message,
            width=self._config["ui"]["window_width"],
            height=self._config["ui"]["window_height"],
        )

        self._start_services()
        self._window.show()

        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(30000)

        exit_code = app.exec()

        self._shutdown()
        sys.exit(exit_code)

    def _start_services(self):
        if self._launcher.is_installed():
            success = self._launcher.start()
            if self._window:
                self._window.status_bar.set_hermes_status(success)
                if not success:
                    self._window.chat_widget.append_message(
                        "system", "Agent 服务启动失败，对话功能暂时不可用。"
                    )
        else:
            if self._window:
                self._window.status_bar.set_hermes_status(False)
                self._window.chat_widget.append_message(
                    "system", "未检测到 Hermes Agent，请先安装。"
                )

        if self._config["monitor"]["enabled"]:
            self._monitor.start()
            if self._window:
                self._window.status_bar.set_monitor_status(True)

        self._summary_gen.check_and_generate_pending()

    def _on_user_message(self, text: str):
        if not self._client.is_connected():
            if self._window:
                self._window.chat_widget.append_message(
                    "system", "Agent 服务异常，对话功能暂时不可用。"
                )
            return

        if self._window:
            self._window.chat_widget.set_input_enabled(False)

        response = self._client.send_message(text)

        if self._window:
            if response:
                self._window.chat_widget.append_message("assistant", response)
            else:
                self._window.chat_widget.append_message(
                    "system", "获取回复失败，请稍后重试。"
                )
            self._window.chat_widget.set_input_enabled(True)

    def _check_health(self):
        hermes_ok = self._launcher.is_healthy()
        monitor_ok = self._monitor.is_running()

        if self._window:
            self._window.status_bar.set_hermes_status(hermes_ok)
            self._window.status_bar.set_monitor_status(monitor_ok)

        if not hermes_ok:
            self._launcher.ensure_running()

    def _shutdown(self):
        logger.info("Shutting down...")
        self._monitor.stop()

        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        self._summary_gen.generate_daily(today)

        from memory.screenshot_cleaner import cleanup_similar, cleanup_expired
        memory_dir = self._config["memory"]["base_dir"]
        cleanup_similar(memory_dir, today, self._config["screenshots"]["cleanup_similarity"])
        cleanup_expired(memory_dir, self._config["screenshots"]["retention_days"])

        logger.info("Shutdown complete")


def main():
    app = PetApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_app_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_app_main.py
git commit -m "feat: application entry point with full lifecycle management"
```

---

