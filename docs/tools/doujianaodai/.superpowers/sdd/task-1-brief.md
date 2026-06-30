### Task 1: Stream Parser — Claude Code stream-json Event Parser

**Files:**
- Create: `app/stream_parser.py`
- Test: `tests/test_stream_parser.py`

**Interfaces:**
- Consumes: nothing (standalone module)
- Produces: `StreamEvent` dataclass with fields `event_type: str`, `content: str`, `metadata: dict`; `parse_stream_event(line: str) -> StreamEvent | None` function. Used by Task 2 (`ClaudeClient.send_message_stream`).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_stream_parser.py
import json
import pytest
from app.stream_parser import StreamEvent, parse_stream_event


def test_parse_init_event():
    line = json.dumps({"type": "system", "subtype": "init", "model": "claude-sonnet-4-20250514", "tools": []})
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "status"
    assert "claude-sonnet" in event.content
    assert event.metadata["model"] == "claude-sonnet-4-20250514"


def test_parse_thinking_event():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "thinking", "thinking": "Let me check the activity..."}]},
    })
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "thinking"
    assert event.content == "Let me check the activity..."


def test_parse_text_event():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "text", "text": "你今天做了三件事"}]},
    })
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "text"
    assert event.content == "你今天做了三件事"


def test_parse_tool_use_event():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": "read_activity_index", "input": {"date": "today"}}]},
    })
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "tool_use"
    assert event.content == "read_activity_index"
    assert event.metadata["input"] == {"date": "today"}


def test_parse_tool_result_event():
    line = json.dumps({
        "type": "assistant",
        "message": {"content": [{"type": "tool_result", "content": "3 activities found"}]},
    })
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "tool_result"
    assert "3 activities" in event.content


def test_parse_result_event():
    line = json.dumps({
        "type": "result",
        "result": "Done",
        "session_id": "abc-123",
        "duration_ms": 4500,
    })
    event = parse_stream_event(line)
    assert event is not None
    assert event.event_type == "done"
    assert event.metadata["session_id"] == "abc-123"


def test_parse_empty_line():
    assert parse_stream_event("") is None
    assert parse_stream_event("   ") is None


def test_parse_invalid_json():
    assert parse_stream_event("not json") is None


def test_parse_unknown_type():
    line = json.dumps({"type": "unknown_thing"})
    event = parse_stream_event(line)
    assert event is None


def test_stream_event_to_dict():
    event = StreamEvent(event_type="text", content="hello", metadata={"key": "val"})
    d = event.to_dict()
    assert d == {"event_type": "text", "content": "hello", "metadata": {"key": "val"}}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_stream_parser.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.stream_parser'`

- [ ] **Step 3: Implement stream_parser.py**

```python
# app/stream_parser.py
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class StreamEvent:
    event_type: str      # "thinking" | "text" | "tool_use" | "tool_result" | "status" | "done"
    content: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"event_type": self.event_type, "content": self.content, "metadata": self.metadata}


def parse_stream_event(line: str) -> StreamEvent | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

    msg_type = data.get("type")

    if msg_type == "system" and data.get("subtype") == "init":
        model = data.get("model", "unknown")
        return StreamEvent(event_type="status", content=f"已连接 {model}", metadata={"model": model})

    if msg_type == "assistant":
        message = data.get("message", data)
        contents = message.get("content", [])
        for item in contents:
            item_type = item.get("type")
            if item_type == "thinking":
                return StreamEvent(event_type="thinking", content=item.get("thinking", ""))
            if item_type == "text":
                return StreamEvent(event_type="text", content=item.get("text", ""))
            if item_type == "tool_use":
                name = item.get("name", "")
                return StreamEvent(
                    event_type="tool_use",
                    content=name,
                    metadata={"input": item.get("input", {})},
                )
            if item_type == "tool_result":
                result_content = item.get("content", "")
                if isinstance(result_content, list):
                    result_content = " ".join(
                        part.get("text", "") for part in result_content if isinstance(part, dict)
                    )
                return StreamEvent(event_type="tool_result", content=str(result_content))
        return None

    if msg_type == "result":
        return StreamEvent(
            event_type="done",
            content=data.get("result", ""),
            metadata={
                "session_id": data.get("session_id", ""),
                "duration_ms": data.get("duration_ms", 0),
            },
        )

    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_stream_parser.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/stream_parser.py tests/test_stream_parser.py
git commit -m "feat: add Claude Code stream-json event parser"
```

---
