import os
import tempfile
import pytest
import app.config as config_module
from app.config import load_config, get_config, DEFAULT_CONFIG


@pytest.fixture(autouse=True)
def reset_config_instance():
    """Reset the global _config_instance before each test to avoid cross-test pollution."""
    config_module._config_instance = None
    yield
    config_module._config_instance = None


def test_default_config_has_required_keys():
    assert "monitor" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["monitor"]["interval_seconds"] == 30
    assert DEFAULT_CONFIG["monitor"]["scenes"] == ["reading", "writing"]
    assert DEFAULT_CONFIG["monitor"]["idle_timeout_seconds"] == 120
    assert DEFAULT_CONFIG["monitor"]["engage_threshold"] == 5
    assert DEFAULT_CONFIG["screenshots"]["quality"] == 75
    assert DEFAULT_CONFIG["screenshots"]["cleanup_similarity"] == 0.9
    assert DEFAULT_CONFIG["screenshots"]["retention_days"] == 7
    assert DEFAULT_CONFIG["ocr"]["engine"] == "paddleocr"
    assert DEFAULT_CONFIG["memory"]["base_dir"] == "./data/pet-memory"
    assert DEFAULT_CONFIG["llm"]["local"]["provider"] == "ollama"


def test_load_config_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("monitor:\n  interval_seconds: 60\n")
        f.flush()
        config = load_config(f.name)
    os.unlink(f.name)
    assert config["monitor"]["interval_seconds"] == 60
    # defaults are preserved for missing keys
    assert config["monitor"]["engage_threshold"] == 5


def test_load_config_missing_file_returns_defaults():
    config = load_config("/nonexistent/path.yaml")
    assert config == DEFAULT_CONFIG


def test_get_config_returns_same_instance():
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2
