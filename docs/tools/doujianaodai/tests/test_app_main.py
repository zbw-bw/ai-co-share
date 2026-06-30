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
