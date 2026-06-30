# Task 10 Report: PyQt6 UI (Main Window + Chat + Status Bar)

## Status: DONE

## What was done

Created three PyQt6 UI components and their smoke tests:

### Files created
- `ui/chat_widget.py` — ChatWidget with QTextEdit display, QLineEdit input, QPushButton send button; emits `message_sent(str)` signal; `append_message(role, content)` renders user/assistant messages with styled HTML bubbles; `set_input_enabled(bool)` for toggling input.
- `ui/status_bar.py` — StatusBar with two QLabels showing Hermes connection status and monitor status; `set_hermes_status(bool)` and `set_monitor_status(bool)` update text and color.
- `ui/main_window.py` — MainWindow (QMainWindow) composing ChatWidget + StatusBar; window title "逗叽脑袋 - 桌面宠物 Agent"; fixed size 400x600; WindowStaysOnTopHint + Tool flags; optional `on_message_sent` callback connected to chat widget signal.
- `tests/test_ui.py` — 3 smoke tests: widget creation, status toggling, main window instantiation.

### Test results
All 3 tests pass (3 passed in 3.19s). PyQt6 was installed during the task (was not present initially).

## Commit
- `a7d89e5` — feat: PyQt6 UI with chat widget and status bar

## Concerns
- PyQt6 was not pre-installed; had to `pip3 install PyQt6` during the task. The `requirements.txt` should include `PyQt6` if not already present (to be verified in Task 12).
- Tests run without `QT_QPA_PLATFORM=offscreen` on macOS — no issues observed with the current smoke tests since `MainWindow.__new__` avoids full initialization.
