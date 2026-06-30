# tests/test_preflight.py
import sys
import pytest
from unittest.mock import patch, MagicMock
from app.preflight import check_python, check_ollama, check_claude_code


def test_check_python_passes():
    assert check_python() is True


def test_check_ollama_running():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "models": [
            {"name": "qwen3:8b"},
            {"name": "llama3:8b"},
        ]
    }
    with patch("requests.get", return_value=mock_response):
        ok, models = check_ollama()
    assert ok is True
    assert "qwen3:8b" in models
    assert "llama3:8b" in models


def test_check_ollama_not_running():
    with patch("requests.get", side_effect=ConnectionError("refused")):
        ok, models = check_ollama()
    assert ok is False
    assert models == []


def test_check_claude_code_available():
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "1.0.28\n"
    with patch("subprocess.run", return_value=mock_result):
        ok, version = check_claude_code()
    assert ok is True
    assert "1.0.28" in version


def test_check_claude_code_not_found():
    with patch("subprocess.run", side_effect=FileNotFoundError()):
        ok, version = check_claude_code()
    assert ok is False
    assert version == ""
