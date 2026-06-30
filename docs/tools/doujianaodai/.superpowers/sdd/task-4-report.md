# Task 4 Report: Menu Bar UI Shell — TrayApp + Tab Container

## Status: DONE

## Commit
- `ad9536a` — feat: add menu bar tray app with 4-tab panel and streaming chat widget

## Files Changed
| File | Action | Lines |
|------|--------|-------|
| `tests/test_ui.py` | Rewritten | 82 |
| `ui/chat_widget.py` | Rewritten | 152 |
| `ui/overview_widget.py` | Created | 58 |
| `ui/activity_log_widget.py` | Created | 94 |
| `ui/settings_widget.py` | Created | 128 |
| `ui/tray_app.py` | Created | 137 |

## What Was Done
1. **tests/test_ui.py** — Rewrote with 7 test functions covering all new widgets:
   - `test_chat_widget_creation` — basic widget + append_message
   - `test_chat_widget_stream_events` — all 6 stream event types
   - `test_chat_widget_clear` — clear_chat resets display
   - `test_overview_widget_creation` — widget instantiation
   - `test_activity_log_widget_creation` — widget instantiation
   - `test_settings_widget_creation` — widget with config dict
   - `test_tray_app_creation` — full TrayApp with status updates

2. **ui/chat_widget.py** — Complete rewrite adding:
   - Header with clear button
   - Status label for streaming feedback
   - `handle_stream_event()` — handles status/thinking/tool_use/tool_result/text/done
   - `clear_chat()` — resets display, status, and thinking state
   - System message role support

3. **ui/overview_widget.py** — New widget:
   - Reads daily stats JSON and activity index
   - Displays screenshot count, engaged sessions, duration, browsing, summaries, messages

4. **ui/activity_log_widget.py** — New widget:
   - Date picker with calendar popup
   - Activity list from index files
   - Detail pane with OCR text stripping
   - Activity count label

5. **ui/settings_widget.py** — New widget:
   - Ollama model dropdown with refresh from API
   - Screenshot interval slider (10-60s)
   - Engage threshold slider (3-10)
   - Retention days spinboxes for screenshots, OCR, logs
   - Save button writes YAML and triggers config reload

6. **ui/tray_app.py** — New tray application:
   - QSystemTrayIcon with emoji-based icon
   - Context menu with monitor/agent status, open data dir, quit
   - 420x520 panel with WindowStaysOnTopHint + FramelessWindowHint + Tool flags
   - 4-tab QTabWidget: Chat, Overview, Activity Log, Settings
   - show_panel/hide_panel positioning near tray icon
   - update_monitor_status/update_agent_status methods

## Test Results
- **7/7 UI tests pass**
- **90/90 tests in tests/ directory pass** (all existing tests unaffected)
- 3 pre-existing failures in root `test_pipeline.py` (missing Quartz module, fixture errors) — not related to this task

## Dependencies Installed
- PyQt6 6.11.0 (was missing from venv, installed via `uv pip install`)

## Interfaces Produced
- `TrayApp(config, config_path, on_message_sent)` — ready for Task 5 (PetApp)
- `ChatWidget.handle_stream_event(event)` — ready for streaming integration
- `OverviewWidget.refresh(stats_dir, index_dir)` — ready for data binding
- `ActivityLogWidget.load_date(index_dir, activities_dir, date)` — ready for data binding
- `SettingsWidget(config, config_path, on_config_changed)` — ready for config management

## Concerns
None.
