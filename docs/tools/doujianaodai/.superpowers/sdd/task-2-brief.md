### Task 2: Streaming ClaudeClient — Add send_message_stream() with Popen

**Files:**
- Modify: `app/claude_client.py`
- Test: `tests/test_claude_client.py` (modify)

**Interfaces:**
- Consumes: `StreamEvent`, `parse_stream_event` from `app.stream_parser` (Task 1)
- Produces: `ClaudeClient.send_message_stream(text: str) -> Generator[StreamEvent, None, None]` method. Used by Task 5 (`ChatWorker` in `app/main.py`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_claude_client.py`:

```python
# tests/test_claude_client.py
import json
import pytest
from unittest.mock import patch, MagicMock
from app.claude_client import ClaudeClient


@pytest.fixture
def client():
    return ClaudeClient()


def test_send_message_stream_yields_events(client):
    lines = [
        json.dumps({"type": "system", "subtype": "init", "model": "claude-sonnet-4-20250514", "tools": []}),
        json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "hello"}]}}),
        json.dumps({"type": "result", "result": "hello", "session_id": "sess-1", "duration_ms": 100}),
    ]

    mock_proc = MagicMock()
    mock_proc.stdout = iter(line + "\n" for line in lines)
    mock_proc.wait.return_value = 0
    mock_proc.returncode = 0

    with patch("subprocess.Popen", return_value=mock_proc):
        events = list(client.send_message_stream("hi"))

    assert len(events) == 3
    assert events[0].event_type == "status"
    assert events[1].event_type == "text"
    assert events[1].content == "hello"
    assert events[2].event_type == "done"
    assert client._session_id == "sess-1"


def test_send_message_stream_handles_popen_error(client):
    with patch("subprocess.Popen", side_effect=FileNotFoundError("claude not found")):
        events = list(client.send_message_stream("hi"))
    assert len(events) == 0


def test_send_message_stream_resumes_session(client):
    client._session_id = "existing-sess"
    mock_proc = MagicMock()
    mock_proc.stdout = iter([])
    mock_proc.wait.return_value = 0
    mock_proc.returncode = 0

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        list(client.send_message_stream("hi"))
    call_args = mock_popen.call_args[0][0]
    assert "--resume" in call_args
    assert "existing-sess" in call_args
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_claude_client.py -v`
Expected: FAIL — `AttributeError: 'ClaudeClient' object has no attribute 'send_message_stream'`

- [ ] **Step 3: Add send_message_stream method to ClaudeClient**

Add these imports at the top of `app/claude_client.py`:

```python
from typing import Generator
from app.stream_parser import StreamEvent, parse_stream_event
```

Add this method to the `ClaudeClient` class, after `send_message`:

```python
    def send_message_stream(self, text: str) -> Generator[StreamEvent, None, None]:
        cmd = ["claude", "-p", text, "--output-format", "stream-json", "--verbose"]
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._project_dir,
            )
            for line in proc.stdout:
                event = parse_stream_event(line)
                if event:
                    if event.event_type == "done" and event.metadata.get("session_id"):
                        self._session_id = event.metadata["session_id"]
                    yield event
            proc.wait()
        except FileNotFoundError:
            logger.error("Claude Code CLI not found")
        except Exception:
            logger.exception("Stream error in Claude Code call")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_claude_client.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run all existing tests**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest -v`
Expected: All 68+ tests PASS (no regressions)

- [ ] **Step 6: Commit**

```bash
git add app/claude_client.py tests/test_claude_client.py
git commit -m "feat: add streaming send_message_stream to ClaudeClient"
```

---
