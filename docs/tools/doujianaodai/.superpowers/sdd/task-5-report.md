# Task 5 Report: Rewire PetApp — TrayApp + Streaming ChatWorker

## Status: DONE

## Commit
- `689013b` — feat: rewire PetApp to use TrayApp with streaming ChatWorker

## Changes Made

### `app/main.py` (rewritten)
- **Import**: Replaced `from ui.main_window import MainWindow` with `from ui.tray_app import TrayApp`
- **ChatWorker**: Changed from `response_ready = pyqtSignal(str)` to `stream_event = pyqtSignal(dict)` + `finished = pyqtSignal()`. Now iterates `send_message_stream` and emits `event.to_dict()` for each stream event.
- **PetApp.__init__**: Now accepts optional `config` and `config_path` params. Stores `_config_path`. Uses `_tray` instead of `_window`.
- **PetApp.run()**: Added `app.setQuitOnLastWindowClosed(False)` for tray-only operation. Creates `TrayApp` instead of `MainWindow`.
- **_start_services()**: Uses `self._tray.update_monitor_status()` instead of `status_bar.set_monitor_status()`. Sets `activity_log_widget.set_base_dir()` and refreshes `overview_widget`.
- **_on_user_message()**: Connects `stream_event` signal to `_on_stream_event`, plus `finished` to `_on_chat_finished`.
- **_on_stream_event()**: New method — forwards stream events to `chat_widget.handle_stream_event()`.
- **_on_chat_finished()**: New method — re-enables input and refreshes overview.
- **main()**: Now calls `run_preflight()` before creating `PetApp`, passes `config` and `config_path`.

### `tests/test_app_main.py` (rewritten)
- `test_pet_app_construction`: Verifies PetApp can be instantiated.
- `test_chat_worker_emits_stream_events`: Verifies ChatWorker emits stream events as dicts with correct structure using `send_message_stream`.

## Test Results
- `tests/test_app_main.py`: 2/2 passed
- Full suite (`tests/`): 91/91 passed
- Pre-existing failures in `test_pipeline.py` (root-level, requires macOS Quartz) — not related to this task.

## Self-Review Checklist
- [x] No import of `MainWindow` remains in `app/main.py`
- [x] `TrayApp` imported from `ui.tray_app`
- [x] `ChatWorker` uses `stream_event = pyqtSignal(dict)` and iterates `send_message_stream`
- [x] `PetApp` accepts optional `config` and `config_path`
- [x] `app.setQuitOnLastWindowClosed(False)` present
- [x] Stream events connected to `chat_widget.handle_stream_event`
- [x] Overview refreshed after chat finishes
- [x] `activity_log_widget.set_base_dir` called in `_start_services`
- [x] `main()` calls `run_preflight()` and passes config to `PetApp`
- [x] All tests pass
