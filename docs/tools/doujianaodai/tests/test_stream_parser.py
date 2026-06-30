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
