# Task 2 Report: Streaming ClaudeClient — Add send_message_stream

## Status: DONE

## Commit
- `6c089bc` — feat: add streaming send_message_stream to ClaudeClient

## What was done

### Modified files
1. **`app/claude_client.py`** — Added `send_message_stream(text: str) -> Generator[StreamEvent, None, None]` method and required imports (`Generator`, `StreamEvent`, `parse_stream_event`).
2. **`tests/test_claude_client.py`** — Added 3 new test functions alongside the 2 existing ones, plus `json`, `pytest` imports and a `client` fixture.

### New method: `send_message_stream`
- Uses `subprocess.Popen` with `stdout=PIPE` for line-by-line streaming.
- Passes `--output-format stream-json --verbose` flags to the Claude CLI.
- Delegates JSON line parsing to `parse_stream_event()` from Task 1.
- Captures `session_id` from `done` events for session resumption.
- Supports `--resume <session_id>` when a session already exists.
- Handles `FileNotFoundError` (CLI not installed) and generic exceptions gracefully.

### New tests
- `test_send_message_stream_yields_events` — verifies 3 events are yielded (status, text, done) and session_id is captured.
- `test_send_message_stream_handles_popen_error` — verifies graceful handling when CLI is missing.
- `test_send_message_stream_resumes_session` — verifies `--resume` flag is included when session exists.

### Existing code
- `send_message()` method is completely unchanged.
- 2 pre-existing tests continue to pass.

## Test summary
- 82 passed, 0 failed, 2 pre-existing errors in `test_pipeline.py` (unrelated fixture issues).

## Concerns
None.
