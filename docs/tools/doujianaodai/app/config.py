import copy
import os
from pathlib import Path

import yaml

DEFAULT_CONFIG = {
    "monitor": {
        "enabled": True,
        "interval_seconds": 30,
        "scenes": ["reading", "writing"],
        "idle_timeout_seconds": 120,
        "engage_threshold": 5,
    },
    "screenshots": {
        "quality": 75,
        "cleanup_similarity": 0.9,
        "retention_days": 7,
    },
    "ocr": {
        "engine": "paddleocr",
        "lang": "ch",
    },
    "llm": {
        "local": {
            "provider": "ollama",
            "model": "qwen3:8b",
            "base_url": "http://localhost:11434",
        },
    },
    "memory": {
        "base_dir": "./data/pet-memory",
        "embedding_model": "bge-small-zh",
    },
    "ui": {
        "window_width": 400,
        "window_height": 600,
    },
}

_config_instance = None


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def load_config(path: str) -> dict:
    global _config_instance
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        _config_instance = _deep_merge(DEFAULT_CONFIG, user_config)
    else:
        _config_instance = copy.deepcopy(DEFAULT_CONFIG)
    return _config_instance


def get_config() -> dict:
    global _config_instance
    if _config_instance is None:
        _config_instance = copy.deepcopy(DEFAULT_CONFIG)
    return _config_instance
