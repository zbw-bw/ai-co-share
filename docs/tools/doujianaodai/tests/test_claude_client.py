import json
import pytest
from unittest.mock import patch, MagicMock
from app.claude_client import ClaudeClient


@patch("app.claude_client.subprocess.run")
def test_send_message_logs_chat(mock_run, tmp_path):
    mock_run.return_value = MagicMock(
        stdout='{"result":"ok","session_id":"s1","is_error":false,"modelUsage":{"Qwen":{}}}',
        returncode=0,
    )
    from logs.pet_logger import ChatLogger, StatsCollector
    chat_logger = ChatLogger(str(tmp_path))
    stats = StatsCollector(str(tmp_path))
    client = ClaudeClient(chat_logger=chat_logger, stats_collector=stats)
    result = client.send_message("hello")
    assert result == "ok"
    log_files = list((tmp_path / "logs" / "chat").rglob("*.md"))
    assert len(log_files) == 1


@patch("app.claude_client.subprocess.run")
def test_send_message_without_logger(mock_run):
    mock_run.return_value = MagicMock(
        stdout='{"result":"ok","session_id":"s1","is_error":false}',
        returncode=0,
    )
    client = ClaudeClient()
    result = client.send_message("hello")
    assert result == "ok"


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
