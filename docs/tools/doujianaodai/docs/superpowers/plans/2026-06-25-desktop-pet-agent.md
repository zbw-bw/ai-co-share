# 桌面宠物 Agent (doujianaodai) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone Windows desktop app that passively monitors screen activity (foreground window screenshots + OCR), stores activity memories as markdown documents with three-tier summaries, and connects to Hermes Agent for conversational AI capabilities.

**Architecture:** A PyQt6 desktop application (main process) launches Hermes Agent as a background gateway service and communicates via HTTP/WebSocket. A passive monitor loop runs in a background thread, capturing foreground window screenshots every 30 seconds, running local PaddleOCR, classifying scenes (reading/writing), and writing activity records as markdown files. A local MCP server exposes custom tools (activity index, detail, screenshot, OCR) to Hermes so the agent can retrieve activity memories during conversation.

**Tech Stack:** Python 3.11+, PyQt6, PyObjC (Quartz/AppKit), Pillow, PaddleOCR, Ollama (Qwen2.5-7B), Hermes Agent, scikit-image (SSIM), numpy, mcp (Python MCP SDK)

## Global Constraints

- Target platform: macOS 12+ (Monterey and above)
- macOS 屏幕录制权限：应用需要在「系统设置 → 隐私与安全 → 屏幕录制」中授权
- All storage is local markdown files — no databases
- All OCR and summarization use local models only (PaddleOCR, Ollama) — no cloud calls from the monitor loop
- Cloud LLM calls happen only through Hermes for user-facing conversation
- Tests must be runnable on macOS by mocking heavy dependencies (PaddleOCR, Ollama)
- Python 3.11+ required
- MVP scenes: reading and writing only — no code/video/chat detection

## Task 0: 前置环境搭建

在开始编码之前，需要确保以下环境就绪。此任务不产出代码，是手动操作。

- [ ] **Step 1: 安装 Ollama**

```bash
# macOS
brew install ollama
# 或
curl -fsSL https://ollama.ai/install.sh | sh
```

- [ ] **Step 2: 拉取本地模型**

```bash
# 启动 Ollama 服务
ollama serve

# 另开终端，拉取 Qwen2.5-7B（约 4.7GB）
ollama pull qwen2.5:7b

# 验证模型可用
ollama run qwen2.5:7b "你好，请用一句话介绍自己"
```

- [ ] **Step 3: 安装 Hermes Agent**

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc  # 或 source ~/.zshrc

# 验证安装
hermes --version

# 配置模型（选择 Ollama 或云端 API）
hermes model

# 快速测试 Hermes 可用
hermes chat -q "Hello"
```

- [ ] **Step 4: 配置 Hermes Gateway**

```bash
# 设置 gateway（用于宠物应用通信）
hermes gateway setup

# 启动 gateway 验证
hermes gateway start
# 另开终端检查健康状态
curl http://localhost:3000/health
# 确认返回 200 后关闭
```

- [ ] **Step 5: 授予屏幕录制权限**

macOS 需要在「系统设置 → 隐私与安全 → 屏幕录制」中授予 Terminal（或 iTerm2）和 Python 截屏权限。首次运行截图代码时系统会弹窗请求授权。

- [ ] **Step 6: 验证 PaddleOCR 可安装**

```bash
pip install paddleocr paddlepaddle
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

环境就绪后进入编码阶段。

---

### Task 1: Project Foundation + Config System

**Files:**
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `config.yaml`
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `monitor/__init__.py`
- Create: `memory/__init__.py`
- Create: `ui/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`
- Create: `.gitignore`

**Interfaces:**
- Produces: `app.config.load_config(path: str) -> dict` — returns parsed config dictionary
- Produces: `app.config.get_config() -> dict` — returns the singleton loaded config
- Produces: `app.config.DEFAULT_CONFIG: dict` — default values used when keys missing

- [ ] **Step 1: Write failing test for config loading**

```python
# tests/test_config.py
import os
import tempfile
import pytest
from app.config import load_config, get_config, DEFAULT_CONFIG


def test_default_config_has_required_keys():
    assert "monitor" in DEFAULT_CONFIG
    assert DEFAULT_CONFIG["monitor"]["interval_seconds"] == 30
    assert DEFAULT_CONFIG["monitor"]["scenes"] == ["reading", "writing"]
    assert DEFAULT_CONFIG["monitor"]["idle_timeout_seconds"] == 120
    assert DEFAULT_CONFIG["monitor"]["confirm_count"] == 2
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
    assert config["monitor"]["confirm_count"] == 2


def test_load_config_missing_file_returns_defaults():
    config = load_config("/nonexistent/path.yaml")
    assert config == DEFAULT_CONFIG


def test_get_config_returns_same_instance():
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/zy/zytest/doujianaodai && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Create project structure and implement config**

```
# .gitignore
data/
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.eggs/
```

```
# requirements.txt
PyQt6>=6.6.0
pyobjc-framework-Quartz>=10.0; sys_platform == "darwin"
pyobjc-framework-AppKit>=10.0; sys_platform == "darwin"
psutil>=5.9.0
Pillow>=10.0.0
paddleocr>=2.7.0
paddlepaddle>=2.6.0
scikit-image>=0.22.0
numpy>=1.26.0
PyYAML>=6.0
requests>=2.31.0
websockets>=12.0
mcp>=1.0.0
ollama>=0.3.0
```

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name="doujianaodai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={"console_scripts": ["doujianaodai=app.main:main"]},
    python_requires=">=3.11",
)
```

```yaml
# config.yaml
monitor:
  enabled: true
  interval_seconds: 30
  scenes:
    - reading
    - writing
  idle_timeout_seconds: 120
  confirm_count: 2

screenshots:
  quality: 75
  cleanup_similarity: 0.9
  retention_days: 7

ocr:
  engine: paddleocr
  lang: ch

llm:
  local:
    provider: ollama
    model: qwen2.5:7b
    base_url: http://localhost:11434

memory:
  base_dir: ./data/pet-memory
  embedding_model: bge-small-zh

ui:
  window_width: 400
  window_height: 600
```

```python
# app/__init__.py
```

```python
# monitor/__init__.py
```

```python
# memory/__init__.py
```

```python
# ui/__init__.py
```

```python
# tests/__init__.py
```

```python
# app/config.py
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
        "confirm_count": 2,
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
            "model": "qwen2.5:7b",
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
```

- [ ] **Step 4: Run tests and verify they pass**

Run: `cd /Users/zy/zytest/doujianaodai && pip install pyyaml && python -m pytest tests/test_config.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/zy/zytest/doujianaodai
git init
git add .
git commit -m "feat: project scaffold with config system"
```

---

### Task 2: Foreground Window Screenshot + Idle Detection

**Files:**
- Create: `monitor/screenshot.py`
- Create: `monitor/idle_detector.py`
- Create: `tests/test_screenshot.py`
- Create: `tests/test_idle_detector.py`

**Interfaces:**
- Consumes: nothing
- Produces: `monitor.screenshot.capture_foreground_window() -> tuple[Image.Image | None, str, str]` — returns (PIL Image or None, window_title, process_name)
- Produces: `monitor.idle_detector.get_idle_seconds() -> float` — returns seconds since last user input
- Produces: `monitor.idle_detector.is_user_idle(timeout: int) -> bool` — True if idle > timeout

- [ ] **Step 1: Write failing tests**

```python
# tests/test_screenshot.py
from unittest.mock import patch, MagicMock
from PIL import Image
from monitor.screenshot import capture_foreground_window


@patch("monitor.screenshot._get_foreground_window_info")
@patch("monitor.screenshot._capture_window_image")
def test_capture_returns_image_and_title(mock_capture, mock_info):
    mock_info.return_value = ("Test Document - Chrome", "Google Chrome", (100, 100, 800, 600))
    mock_capture.return_value = Image.new("RGB", (700, 500), color="white")

    image, title, process = capture_foreground_window()

    assert image is not None
    assert image.size == (700, 500)
    assert title == "Test Document - Chrome"
    assert process == "Google Chrome"


@patch("monitor.screenshot._get_foreground_window_info")
def test_capture_returns_none_when_no_window(mock_info):
    mock_info.return_value = (None, None, None)

    image, title, process = capture_foreground_window()

    assert image is None
    assert title is None
    assert process is None
```

```python
# tests/test_idle_detector.py
from unittest.mock import patch
from monitor.idle_detector import get_idle_seconds, is_user_idle


@patch("monitor.idle_detector._get_idle_seconds_macos")
def test_get_idle_seconds(mock_idle):
    mock_idle.return_value = 3.0
    assert get_idle_seconds() == 3.0


@patch("monitor.idle_detector.get_idle_seconds")
def test_is_user_idle_true(mock_idle):
    mock_idle.return_value = 150.0
    assert is_user_idle(120) is True


@patch("monitor.idle_detector.get_idle_seconds")
def test_is_user_idle_false(mock_idle):
    mock_idle.return_value = 30.0
    assert is_user_idle(120) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_screenshot.py tests/test_idle_detector.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement screenshot and idle detector (macOS)**

```python
# monitor/screenshot.py
"""Foreground window screenshot capture using macOS Quartz API.

Requires screen recording permission in System Settings → Privacy & Security.
"""
from __future__ import annotations

import sys
from typing import Optional

from PIL import Image

_IS_MACOS = sys.platform == "darwin"


def _get_foreground_window_info() -> tuple[Optional[str], Optional[str], Optional[tuple]]:
    if not _IS_MACOS:
        return None, None, None

    import Quartz
    import AppKit

    app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    if not app:
        return None, None, None

    app_name = app.localizedName() or "unknown"
    pid = app.processIdentifier()

    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )

    for window in window_list:
        if window.get(Quartz.kCGWindowOwnerPID) == pid:
            title = window.get(Quartz.kCGWindowName, "")
            if not title:
                continue
            bounds = window.get(Quartz.kCGWindowBounds, {})
            x = int(bounds.get("X", 0))
            y = int(bounds.get("Y", 0))
            w = int(bounds.get("Width", 0))
            h = int(bounds.get("Height", 0))
            if w > 0 and h > 0:
                return title, app_name, (x, y, w, h)

    return None, None, None


def _capture_window_image(rect: tuple) -> Optional[Image.Image]:
    if not _IS_MACOS:
        return None

    import Quartz

    x, y, w, h = rect
    cg_rect = Quartz.CGRectMake(x, y, w, h)
    cg_image = Quartz.CGWindowListCreateImage(
        cg_rect,
        Quartz.kCGWindowListOptionOnScreenOnly,
        Quartz.kCGNullWindowID,
        Quartz.kCGWindowImageDefault,
    )

    if cg_image is None:
        return None

    width = Quartz.CGImageGetWidth(cg_image)
    height = Quartz.CGImageGetHeight(cg_image)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)
    data_provider = Quartz.CGImageGetDataProvider(cg_image)
    data = Quartz.CGDataProviderCopyData(data_provider)

    image = Image.frombuffer(
        "RGBA", (width, height), data, "raw", "BGRA", bytes_per_row, 1,
    )
    return image.convert("RGB")


def capture_foreground_window() -> tuple[Optional[Image.Image], Optional[str], Optional[str]]:
    title, app_name, rect = _get_foreground_window_info()
    if title is None or rect is None:
        return None, None, None
    image = _capture_window_image(rect)
    return image, title, app_name
```

```python
# monitor/idle_detector.py
"""User idle detection via macOS Quartz CGEventSource.

Reports seconds since last keyboard/mouse event.
"""
from __future__ import annotations

import sys

_IS_MACOS = sys.platform == "darwin"


def _get_idle_seconds_macos() -> float:
    if not _IS_MACOS:
        return 0.0

    import Quartz

    idle_time = Quartz.CGEventSourceSecondsSinceLastEventType(
        Quartz.kCGEventSourceStateCombinedSessionState,
        Quartz.kCGAnyInputEventType,
    )
    return float(idle_time)


def get_idle_seconds() -> float:
    return _get_idle_seconds_macos()


def is_user_idle(timeout: int = 120) -> bool:
    return get_idle_seconds() > timeout
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_screenshot.py tests/test_idle_detector.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/screenshot.py monitor/idle_detector.py tests/test_screenshot.py tests/test_idle_detector.py
git commit -m "feat: foreground window screenshot and idle detection (macOS)"
```

---

### Task 3: OCR + Scene Classification

**Files:**
- Create: `monitor/ocr.py`
- Create: `monitor/scene_classifier.py`
- Create: `tests/test_ocr.py`
- Create: `tests/test_scene_classifier.py`

**Interfaces:**
- Consumes: `PIL.Image.Image` from Task 2
- Produces: `monitor.ocr.recognize_text(image: Image.Image) -> str` — returns OCR text
- Produces: `monitor.scene_classifier.classify_scene(window_title: str, process_name: str, ocr_text: str) -> SceneResult` where `SceneResult` has fields `scene_type: str | None` ("reading" | "writing" | None), `title: str`, `app_name: str`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ocr.py
from unittest.mock import patch, MagicMock
from PIL import Image
from monitor.ocr import recognize_text, OcrEngine


def test_recognize_text_returns_string():
    engine = OcrEngine.__new__(OcrEngine)
    engine._ocr = MagicMock()
    engine._ocr.ocr.return_value = [
        [
            [[[0, 0], [100, 0], [100, 20], [0, 20]], ("Hello World", 0.95)],
            [[[0, 30], [100, 30], [100, 50], [0, 50]], ("测试文本", 0.90)],
        ]
    ]

    text = engine.recognize(Image.new("RGB", (200, 100)))
    assert "Hello World" in text
    assert "测试文本" in text


def test_recognize_text_empty_image():
    engine = OcrEngine.__new__(OcrEngine)
    engine._ocr = MagicMock()
    engine._ocr.ocr.return_value = [[]]

    text = engine.recognize(Image.new("RGB", (200, 100)))
    assert text == ""
```

```python
# tests/test_scene_classifier.py
from monitor.scene_classifier import classify_scene, SceneResult


def test_classify_reading_chrome():
    result = classify_scene(
        window_title="LangGraph教程 - 掘金",
        process_name="Google Chrome",
        ocr_text="LangGraph 是一个用于构建有状态多角色应用的框架。" * 10,
    )
    assert result.scene_type == "reading"
    assert "LangGraph教程" in result.title


def test_classify_writing_word():
    result = classify_scene(
        window_title="产品需求文档.docx",
        process_name="Microsoft Word",
        ocr_text="1. 功能概述\n2. 用户故事\n3. 技术方案",
    )
    assert result.scene_type == "writing"
    assert "产品需求文档" in result.title


def test_classify_skip_unknown_app():
    result = classify_scene(
        window_title="Steam",
        process_name="Steam",
        ocr_text="Play games",
    )
    assert result.scene_type is None


def test_classify_reading_needs_enough_text():
    result = classify_scene(
        window_title="Google Chrome",
        process_name="Google Chrome",
        ocr_text="Hi",
    )
    assert result.scene_type is None


def test_classify_writing_pages():
    result = classify_scene(
        window_title="报告",
        process_name="Pages",
        ocr_text="本季度工作总结\n一、项目进展\n二、存在问题",
    )
    assert result.scene_type == "writing"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_ocr.py tests/test_scene_classifier.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement OCR and scene classifier**

```python
# monitor/ocr.py
from __future__ import annotations

import io
import numpy as np
from PIL import Image


class OcrEngine:
    def __init__(self, lang: str = "ch"):
        from paddleocr import PaddleOCR
        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def recognize(self, image: Image.Image) -> str:
        img_array = np.array(image)
        results = self._ocr.ocr(img_array, cls=True)
        if not results or not results[0]:
            return ""
        lines = []
        for line in results[0]:
            if line and len(line) >= 2:
                text, confidence = line[1]
                if confidence > 0.5:
                    lines.append(text)
        return "\n".join(lines)


_engine: OcrEngine | None = None


def recognize_text(image: Image.Image, lang: str = "ch") -> str:
    global _engine
    if _engine is None:
        _engine = OcrEngine(lang=lang)
    return _engine.recognize(image)
```

```python
# monitor/scene_classifier.py
from __future__ import annotations

import re
from dataclasses import dataclass

READING_PROCESSES = {
    "google chrome", "safari", "microsoft edge", "firefox", "brave browser",
    "arc", "preview", "adobe acrobat reader", "skim",
}

WRITING_PROCESSES = {
    "microsoft word", "pages", "wps office", "notion", "obsidian",
    "typora", "mark text", "microsoft excel", "numbers", "keynote",
    "microsoft powerpoint",
}

MIN_TEXT_LENGTH_FOR_READING = 50


@dataclass
class SceneResult:
    scene_type: str | None
    title: str
    app_name: str


def _extract_document_title(window_title: str) -> str:
    parts = re.split(r"\s[-–—|]\s", window_title)
    if parts:
        return parts[0].strip()
    return window_title.strip()


def classify_scene(
    window_title: str,
    process_name: str,
    ocr_text: str,
) -> SceneResult:
    proc = process_name.lower()
    doc_title = _extract_document_title(window_title)

    if proc in WRITING_PROCESSES:
        if len(ocr_text.strip()) > 10:
            return SceneResult(
                scene_type="writing",
                title=doc_title,
                app_name=process_name,
            )

    if proc in READING_PROCESSES:
        if len(ocr_text.strip()) >= MIN_TEXT_LENGTH_FOR_READING:
            return SceneResult(
                scene_type="reading",
                title=doc_title,
                app_name=process_name,
            )

    return SceneResult(scene_type=None, title=doc_title, app_name=process_name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ocr.py tests/test_scene_classifier.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/ocr.py monitor/scene_classifier.py tests/test_ocr.py tests/test_scene_classifier.py
git commit -m "feat: OCR engine and scene classifier (reading/writing)"
```

---

### Task 4: Activity Memory Writer + Merger

**Files:**
- Create: `memory/activity_writer.py`
- Create: `memory/activity_merger.py`
- Create: `tests/test_activity_writer.py`
- Create: `tests/test_activity_merger.py`

**Interfaces:**
- Consumes: `monitor.scene_classifier.SceneResult` from Task 3
- Produces: `memory.activity_writer.ActivityWriter` class with methods:
  - `write_activity(date: str, start_time: str, end_time: str, scene_type: str, title: str, app_name: str, summary: str, content: str, screenshot_paths: list[str]) -> str` — writes activity md file, updates index, returns file path
  - `update_activity(file_path: str, end_time: str, additional_content: str, screenshot_paths: list[str]) -> None` — updates existing activity's end time and content
- Produces: `memory.activity_merger.ActivityMerger` class with methods:
  - `process(scene: SceneResult, timestamp: str) -> MergeAction` where MergeAction has `action: str` ("pending" | "new" | "merge" | "skip"), `activity_path: str | None`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_activity_writer.py
import os
import tempfile
import shutil
from memory.activity_writer import ActivityWriter


def test_write_activity_creates_files():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        path = writer.write_activity(
            date="2026-06-25",
            start_time="10:00",
            end_time="10:35",
            scene_type="reading",
            title="LangGraph教程",
            app_name="Chrome",
            summary="阅读了LangGraph工作流编排教程",
            content="用户在Chrome中阅读了一篇关于LangGraph工作流编排的技术文章。",
            screenshot_paths=["screenshots/2026-06-25/10-00-00.jpg"],
        )

        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "LangGraph教程" in content
        assert "10:00-10:35" in content
        assert "阅读" in content

        index_path = os.path.join(base_dir, "index", "2026-06-25.md")
        assert os.path.exists(index_path)
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()
        assert "LangGraph教程" in index_content
    finally:
        shutil.rmtree(base_dir)


def test_update_activity_extends_time():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        path = writer.write_activity(
            date="2026-06-25",
            start_time="10:00",
            end_time="10:05",
            scene_type="reading",
            title="Test Article",
            app_name="Chrome",
            summary="Reading an article",
            content="Initial content.",
            screenshot_paths=[],
        )
        writer.update_activity(
            file_path=path,
            end_time="10:35",
            additional_content="More details discovered.",
            screenshot_paths=["screenshots/new.jpg"],
        )

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "10:00-10:35" in content
        assert "More details discovered" in content
        assert "screenshots/new.jpg" in content
    finally:
        shutil.rmtree(base_dir)


def test_write_multiple_activities_same_day():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        writer.write_activity("2026-06-25", "10:00", "10:35", "reading",
                              "Article A", "Chrome", "Read A", "Content A", [])
        writer.write_activity("2026-06-25", "10:40", "11:20", "writing",
                              "Doc B", "WPS", "Wrote B", "Content B", [])

        index_path = os.path.join(base_dir, "index", "2026-06-25.md")
        with open(index_path, "r", encoding="utf-8") as f:
            lines = f.read()
        assert "Article A" in lines
        assert "Doc B" in lines
    finally:
        shutil.rmtree(base_dir)
```

```python
# tests/test_activity_merger.py
from memory.activity_merger import ActivityMerger
from monitor.scene_classifier import SceneResult


def test_first_observation_is_pending():
    merger = ActivityMerger(confirm_count=2)
    result = merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:00",
    )
    assert result.action == "pending"


def test_second_same_observation_confirms():
    merger = ActivityMerger(confirm_count=2)
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:00",
    )
    result = merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:30",
    )
    assert result.action == "new"


def test_continued_same_activity_merges():
    merger = ActivityMerger(confirm_count=2)
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:00",
    )
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:30",
    )
    result = merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:01:00",
    )
    assert result.action == "merge"


def test_different_activity_resets():
    merger = ActivityMerger(confirm_count=2)
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:00",
    )
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:30",
    )
    result = merger.process(
        SceneResult(scene_type="writing", title="Doc B", app_name="Pages"),
        timestamp="2026-06-25 10:01:00",
    )
    assert result.action == "pending"


def test_none_scene_skips():
    merger = ActivityMerger(confirm_count=2)
    result = merger.process(
        SceneResult(scene_type=None, title="Steam", app_name="Steam"),
        timestamp="2026-06-25 10:00:00",
    )
    assert result.action == "skip"


def test_pending_dropped_when_different_activity_arrives():
    merger = ActivityMerger(confirm_count=2)
    merger.process(
        SceneResult(scene_type="reading", title="Article A", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:00",
    )
    result = merger.process(
        SceneResult(scene_type="reading", title="Article B", app_name="Google Chrome"),
        timestamp="2026-06-25 10:00:30",
    )
    assert result.action == "pending"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_activity_writer.py tests/test_activity_merger.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement activity writer and merger**

```python
# memory/activity_writer.py
from __future__ import annotations

import os
import re
from pathlib import Path


class ActivityWriter:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)
        self._counters: dict[str, int] = {}

    def _next_id(self, date: str) -> int:
        if date not in self._counters:
            activities_dir = self._base_dir / "activities" / date
            if activities_dir.exists():
                existing = list(activities_dir.glob("activity_*.md"))
                nums = []
                for f in existing:
                    m = re.search(r"activity_(\d+)\.md", f.name)
                    if m:
                        nums.append(int(m.group(1)))
                self._counters[date] = max(nums) if nums else 0
            else:
                self._counters[date] = 0
        self._counters[date] += 1
        return self._counters[date]

    def write_activity(
        self,
        date: str,
        start_time: str,
        end_time: str,
        scene_type: str,
        title: str,
        app_name: str,
        summary: str,
        content: str,
        screenshot_paths: list[str],
    ) -> str:
        activity_id = self._next_id(date)
        activity_dir = self._base_dir / "activities" / date
        activity_dir.mkdir(parents=True, exist_ok=True)

        filename = f"activity_{activity_id:03d}.md"
        file_path = activity_dir / filename

        scene_label = "阅读" if scene_type == "reading" else "写作"
        screenshots_line = ""
        if screenshot_paths:
            screenshots_line = f"截图：{', '.join(screenshot_paths)}\n"

        doc = (
            f"时间：{date} {start_time}-{end_time}\n"
            f"场景：{scene_label}\n"
            f"来源：{app_name}\n"
            f"标签：{self._generate_tags(scene_type)}\n"
            f"{screenshots_line}\n"
            f"{content}\n"
        )

        file_path.write_text(doc, encoding="utf-8")
        self._update_index(date, start_time, end_time, scene_type, title, file_path)
        return str(file_path)

    def update_activity(
        self,
        file_path: str,
        end_time: str,
        additional_content: str,
        screenshot_paths: list[str],
    ) -> None:
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")

        text = re.sub(
            r"(时间：\S+\s+\S+)-\S+",
            rf"\1-{end_time}",
            text,
        )

        if additional_content:
            text = text.rstrip() + f"\n{additional_content}\n"

        if screenshot_paths:
            if "截图：" in text:
                text = re.sub(
                    r"(截图：[^\n]*)",
                    rf"\1, {', '.join(screenshot_paths)}",
                    text,
                )
            else:
                text = text.replace(
                    "\n\n",
                    f"\n截图：{', '.join(screenshot_paths)}\n\n",
                    1,
                )

        path.write_text(text, encoding="utf-8")

    def _update_index(
        self, date: str, start_time: str, end_time: str,
        scene_type: str, title: str, activity_path: Path,
    ) -> None:
        index_dir = self._base_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / f"{date}.md"

        rel_path = activity_path.relative_to(self._base_dir)
        tag = "#阅读" if scene_type == "reading" else "#写作"
        category_tag = "#学习" if scene_type == "reading" else "#工作"
        line = f"- [{start_time}-{end_time}] {category_tag} {tag} {title} → {rel_path}\n"

        if index_path.exists():
            existing = index_path.read_text(encoding="utf-8")
            index_path.write_text(existing + line, encoding="utf-8")
        else:
            header = f"# {date} 活动索引\n\n"
            index_path.write_text(header + line, encoding="utf-8")

    def _generate_tags(self, scene_type: str) -> str:
        if scene_type == "reading":
            return "学习、阅读"
        return "工作、写作"
```

```python
# memory/activity_merger.py
from __future__ import annotations

from dataclasses import dataclass
from monitor.scene_classifier import SceneResult


@dataclass
class MergeAction:
    action: str  # "pending" | "new" | "merge" | "skip"
    activity_path: str | None = None


class ActivityMerger:
    def __init__(self, confirm_count: int = 2):
        self._confirm_count = confirm_count
        self._pending: SceneResult | None = None
        self._pending_count: int = 0
        self._pending_timestamp: str | None = None
        self._current: SceneResult | None = None
        self._current_path: str | None = None

    def set_current_path(self, path: str) -> None:
        self._current_path = path

    def process(self, scene: SceneResult, timestamp: str) -> MergeAction:
        if scene.scene_type is None:
            return MergeAction(action="skip")

        if self._current and self._is_same(scene, self._current):
            return MergeAction(action="merge", activity_path=self._current_path)

        if self._pending and self._is_same(scene, self._pending):
            self._pending_count += 1
            if self._pending_count >= self._confirm_count:
                self._current = self._pending
                self._pending = None
                self._pending_count = 0
                return MergeAction(action="new")
            return MergeAction(action="pending")

        self._pending = scene
        self._pending_count = 1
        self._pending_timestamp = timestamp
        self._current = None
        self._current_path = None
        return MergeAction(action="pending")

    def _is_same(self, a: SceneResult, b: SceneResult) -> bool:
        return a.scene_type == b.scene_type and a.title == b.title
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_activity_writer.py tests/test_activity_merger.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add memory/ tests/test_activity_writer.py tests/test_activity_merger.py
git commit -m "feat: activity memory writer with index and merger with two-shot confirmation"
```

---

### Task 5: Screenshot Storage + SSIM Cleanup

**Files:**
- Create: `memory/screenshot_cleaner.py`
- Create: `tests/test_screenshot_cleaner.py`

**Interfaces:**
- Consumes: `PIL.Image.Image` from Task 2
- Produces: `memory.screenshot_cleaner.save_screenshot(image: Image.Image, base_dir: str, date: str, timestamp: str, quality: int) -> str` — saves JPEG, returns path
- Produces: `memory.screenshot_cleaner.cleanup_similar(base_dir: str, date: str, similarity_threshold: float) -> int` — removes similar frames, returns count removed
- Produces: `memory.screenshot_cleaner.cleanup_expired(base_dir: str, retention_days: int) -> int` — removes old dirs, returns count removed

- [ ] **Step 1: Write failing tests**

```python
# tests/test_screenshot_cleaner.py
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from PIL import Image
from memory.screenshot_cleaner import save_screenshot, cleanup_similar, cleanup_expired


def test_save_screenshot_creates_jpeg():
    base_dir = tempfile.mkdtemp()
    try:
        img = Image.new("RGB", (800, 600), color="blue")
        path = save_screenshot(img, base_dir, "2026-06-25", "10-00-00", quality=75)
        assert os.path.exists(path)
        assert path.endswith(".jpg")
        saved = Image.open(path)
        assert saved.size == (800, 600)
    finally:
        shutil.rmtree(base_dir)


def test_cleanup_similar_removes_duplicates():
    base_dir = tempfile.mkdtemp()
    try:
        screenshot_dir = os.path.join(base_dir, "screenshots", "2026-06-25")
        os.makedirs(screenshot_dir)
        img = Image.new("RGB", (100, 100), color="red")
        img.save(os.path.join(screenshot_dir, "10-00-00.jpg"))
        img.save(os.path.join(screenshot_dir, "10-00-30.jpg"))
        img.save(os.path.join(screenshot_dir, "10-01-00.jpg"))
        different = Image.new("RGB", (100, 100), color="green")
        different.save(os.path.join(screenshot_dir, "10-01-30.jpg"))

        removed = cleanup_similar(base_dir, "2026-06-25", similarity_threshold=0.9)
        assert removed == 1  # middle identical frame removed, keep first, last, and different
        remaining = os.listdir(screenshot_dir)
        assert "10-00-00.jpg" in remaining  # first
        assert "10-01-00.jpg" not in remaining or "10-00-30.jpg" not in remaining
        assert "10-01-30.jpg" in remaining  # different color
    finally:
        shutil.rmtree(base_dir)


def test_cleanup_expired_removes_old_dirs():
    base_dir = tempfile.mkdtemp()
    try:
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        new_date = datetime.now().strftime("%Y-%m-%d")

        old_dir = os.path.join(base_dir, "screenshots", old_date)
        new_dir = os.path.join(base_dir, "screenshots", new_date)
        os.makedirs(old_dir)
        os.makedirs(new_dir)

        Image.new("RGB", (10, 10)).save(os.path.join(old_dir, "test.jpg"))
        Image.new("RGB", (10, 10)).save(os.path.join(new_dir, "test.jpg"))

        removed = cleanup_expired(base_dir, retention_days=7)
        assert removed == 1
        assert not os.path.exists(old_dir)
        assert os.path.exists(new_dir)
    finally:
        shutil.rmtree(base_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_screenshot_cleaner.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement screenshot cleaner**

```python
# memory/screenshot_cleaner.py
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image


def save_screenshot(
    image: Image.Image,
    base_dir: str,
    date: str,
    timestamp: str,
    quality: int = 75,
) -> str:
    screenshot_dir = Path(base_dir) / "screenshots" / date
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{timestamp}.jpg"
    path = screenshot_dir / filename
    image.save(str(path), "JPEG", quality=quality)
    return str(path)


def _compute_ssim_simple(img1: np.ndarray, img2: np.ndarray) -> float:
    if img1.shape != img2.shape:
        return 0.0
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    mu1 = img1.mean()
    mu2 = img2.mean()
    sigma1_sq = img1.var()
    sigma2_sq = img2.var()
    sigma12 = ((img1 - mu1) * (img2 - mu2)).mean()
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)
    )
    return float(ssim)


def cleanup_similar(
    base_dir: str,
    date: str,
    similarity_threshold: float = 0.9,
) -> int:
    screenshot_dir = Path(base_dir) / "screenshots" / date
    if not screenshot_dir.exists():
        return 0

    files = sorted(screenshot_dir.glob("*.jpg"))
    if len(files) <= 2:
        return 0

    to_remove = set()
    images = []
    for f in files:
        img = Image.open(f).convert("L").resize((64, 64))
        images.append(np.array(img))

    for i in range(1, len(files) - 1):
        prev_sim = _compute_ssim_simple(images[i - 1], images[i])
        next_sim = _compute_ssim_simple(images[i], images[i + 1])
        if prev_sim > similarity_threshold and next_sim > similarity_threshold:
            to_remove.add(files[i])

    for f in to_remove:
        f.unlink()
    return len(to_remove)


def cleanup_expired(base_dir: str, retention_days: int = 7) -> int:
    screenshot_dir = Path(base_dir) / "screenshots"
    if not screenshot_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for d in screenshot_dir.iterdir():
        if not d.is_dir():
            continue
        try:
            dir_date = datetime.strptime(d.name, "%Y-%m-%d")
            if dir_date < cutoff:
                shutil.rmtree(d)
                removed += 1
        except ValueError:
            continue
    return removed
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_screenshot_cleaner.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add memory/screenshot_cleaner.py tests/test_screenshot_cleaner.py
git commit -m "feat: screenshot storage with SSIM dedup and expiry cleanup"
```

---

### Task 6: Screen Monitor Main Loop

**Files:**
- Create: `monitor/screen_monitor.py`
- Create: `monitor/llm_client.py`
- Create: `tests/test_screen_monitor.py`

**Interfaces:**
- Consumes: All monitor modules (Task 2-3), memory modules (Task 4-5)
- Produces: `monitor.screen_monitor.ScreenMonitor` class with methods:
  - `start() -> None` — starts background monitoring thread
  - `stop() -> None` — stops monitoring
  - `is_running() -> bool`
- Produces: `monitor.llm_client.generate_summary(ocr_text: str, window_title: str, scene_type: str) -> tuple[str, str]` — returns (one_line_summary, full_content)

- [ ] **Step 1: Write failing tests**

```python
# tests/test_screen_monitor.py
import time
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from PIL import Image
from monitor.screen_monitor import ScreenMonitor
from monitor.scene_classifier import SceneResult


def test_monitor_start_stop():
    base_dir = tempfile.mkdtemp()
    try:
        monitor = ScreenMonitor(
            base_dir=base_dir,
            interval=0.1,
            idle_timeout=120,
            confirm_count=2,
            screenshot_quality=75,
        )
        monitor.start()
        assert monitor.is_running()
        monitor.stop()
        time.sleep(0.2)
        assert not monitor.is_running()
    finally:
        shutil.rmtree(base_dir)


@patch("monitor.screen_monitor.capture_foreground_window")
@patch("monitor.screen_monitor.is_user_idle")
@patch("monitor.screen_monitor.recognize_text")
@patch("monitor.screen_monitor.classify_scene")
@patch("monitor.screen_monitor.generate_summary")
def test_monitor_processes_reading_scene(
    mock_summary, mock_classify, mock_ocr, mock_idle, mock_capture,
):
    base_dir = tempfile.mkdtemp()
    try:
        mock_idle.return_value = False
        mock_capture.return_value = (
            Image.new("RGB", (100, 100)),
            "Article - Chrome",
            "Google Chrome",
        )
        mock_ocr.return_value = "Long article text " * 20
        mock_classify.return_value = SceneResult(
            scene_type="reading", title="Article", app_name="Google Chrome",
        )
        mock_summary.return_value = ("阅读了Article", "用户在Chrome中阅读了Article的详细内容。")

        monitor = ScreenMonitor(
            base_dir=base_dir,
            interval=0.1,
            idle_timeout=120,
            confirm_count=1,  # set to 1 for quick test
            screenshot_quality=75,
        )
        monitor._tick()
        monitor._tick()  # second tick to confirm

        import os
        index_dir = os.path.join(base_dir, "index")
        assert os.path.exists(index_dir)
    finally:
        shutil.rmtree(base_dir)


@patch("monitor.screen_monitor.capture_foreground_window")
@patch("monitor.screen_monitor.is_user_idle")
def test_monitor_skips_when_idle(mock_idle, mock_capture):
    base_dir = tempfile.mkdtemp()
    try:
        mock_idle.return_value = True
        mock_capture.return_value = (Image.new("RGB", (100, 100)), "Doc", "Microsoft Word")

        monitor = ScreenMonitor(
            base_dir=base_dir,
            interval=0.1,
            idle_timeout=120,
            confirm_count=2,
            screenshot_quality=75,
        )
        monitor._tick()
        mock_capture.assert_not_called()  # should skip before capture
    finally:
        shutil.rmtree(base_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_screen_monitor.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement monitor loop and LLM client**

```python
# monitor/llm_client.py
from __future__ import annotations

import requests
import json


def generate_summary(
    ocr_text: str,
    window_title: str,
    scene_type: str,
    base_url: str = "http://localhost:11434",
    model: str = "qwen2.5:7b",
) -> tuple[str, str]:
    scene_label = "阅读文章/文档" if scene_type == "reading" else "编写文档"
    prompt = (
        f"用户正在{scene_label}。\n"
        f"窗口标题：{window_title}\n"
        f"页面内容（OCR识别）：\n{ocr_text[:2000]}\n\n"
        f"请生成两部分内容：\n"
        f"1. 一句话摘要（20字以内）\n"
        f"2. 详细描述（50-100字，描述用户在做什么，内容要点是什么）\n\n"
        f"格式：\n摘要：...\n详细：..."
    )

    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")

        summary = ""
        detail = ""
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("摘要：") or line.startswith("摘要:"):
                summary = line.split("：", 1)[-1].split(":", 1)[-1].strip()
            elif line.startswith("详细：") or line.startswith("详细:"):
                detail = line.split("：", 1)[-1].split(":", 1)[-1].strip()

        if not summary:
            summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"
        if not detail:
            detail = f"用户在{window_title}中进行了{scene_label}活动。"

        return summary, detail
    except Exception:
        summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"
        detail = f"用户在{window_title}中进行了{scene_label}活动。"
        return summary, detail
```

```python
# monitor/screen_monitor.py
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime

from monitor.screenshot import capture_foreground_window
from monitor.idle_detector import is_user_idle
from monitor.ocr import recognize_text
from monitor.scene_classifier import classify_scene
from monitor.llm_client import generate_summary
from memory.activity_writer import ActivityWriter
from memory.activity_merger import ActivityMerger
from memory.screenshot_cleaner import save_screenshot

logger = logging.getLogger(__name__)


class ScreenMonitor:
    def __init__(
        self,
        base_dir: str,
        interval: float = 30.0,
        idle_timeout: int = 120,
        confirm_count: int = 2,
        screenshot_quality: int = 75,
        llm_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ):
        self._base_dir = base_dir
        self._interval = interval
        self._idle_timeout = idle_timeout
        self._screenshot_quality = screenshot_quality
        self._llm_base_url = llm_base_url
        self._llm_model = llm_model

        self._writer = ActivityWriter(base_dir)
        self._merger = ActivityMerger(confirm_count=confirm_count)

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                logger.exception("Monitor tick failed")
            self._stop_event.wait(self._interval)

    def _tick(self) -> None:
        if is_user_idle(self._idle_timeout):
            return

        image, title, process = capture_foreground_window()
        if image is None:
            return

        ocr_text = recognize_text(image)
        scene = classify_scene(title, process, ocr_text)

        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        action = self._merger.process(scene, timestamp_str)

        if action.action == "skip" or action.action == "pending":
            return

        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        ts_for_file = now.strftime("%H-%M-%S")

        screenshot_path = save_screenshot(
            image, self._base_dir, date_str, ts_for_file,
            quality=self._screenshot_quality,
        )

        if action.action == "new":
            summary, content = generate_summary(
                ocr_text, title, scene.scene_type,
                self._llm_base_url, self._llm_model,
            )
            path = self._writer.write_activity(
                date=date_str,
                start_time=time_str,
                end_time=time_str,
                scene_type=scene.scene_type,
                title=scene.title,
                app_name=scene.app_name,
                summary=summary,
                content=content,
                screenshot_paths=[screenshot_path],
            )
            self._merger.set_current_path(path)

        elif action.action == "merge" and action.activity_path:
            self._writer.update_activity(
                file_path=action.activity_path,
                end_time=time_str,
                additional_content="",
                screenshot_paths=[screenshot_path],
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_screen_monitor.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/screen_monitor.py monitor/llm_client.py tests/test_screen_monitor.py
git commit -m "feat: screen monitor main loop with background thread"
```

---

### Task 7: Summary Generator (Daily / Weekly / Monthly)

**Files:**
- Create: `memory/summary_generator.py`
- Create: `tests/test_summary_generator.py`

**Interfaces:**
- Consumes: Activity index files from Task 4, `monitor.llm_client.generate_summary` pattern
- Produces: `memory.summary_generator.SummaryGenerator` class with methods:
  - `generate_daily(date: str) -> str` — generates daily summary, returns path
  - `generate_weekly(year: int, week: int) -> str` — generates weekly summary, returns path
  - `generate_monthly(year: int, month: int) -> str` — generates monthly summary, returns path
  - `check_and_generate_pending() -> list[str]` — checks for missing summaries and generates them

- [ ] **Step 1: Write failing tests**

```python
# tests/test_summary_generator.py
import os
import tempfile
import shutil
from unittest.mock import patch
from memory.summary_generator import SummaryGenerator


def _setup_daily_index(base_dir: str, date: str, content: str) -> None:
    index_dir = os.path.join(base_dir, "index")
    os.makedirs(index_dir, exist_ok=True)
    with open(os.path.join(index_dir, f"{date}.md"), "w", encoding="utf-8") as f:
        f.write(content)


@patch("memory.summary_generator._call_local_llm")
def test_generate_daily_summary(mock_llm):
    base_dir = tempfile.mkdtemp()
    try:
        _setup_daily_index(base_dir, "2026-06-25", (
            "# 2026-06-25 活动索引\n\n"
            "- [10:00-10:35] #学习 #阅读 阅读了LangGraph教程\n"
            "- [10:40-11:20] #工作 #写作 编写了PRD文档\n"
        ))
        mock_llm.return_value = (
            "# 2026-06-25 每日总结\n\n"
            "## 学习\n- 阅读了LangGraph教程\n\n"
            "## 工作\n- 编写了PRD文档\n"
        )

        gen = SummaryGenerator(base_dir)
        path = gen.generate_daily("2026-06-25")

        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "LangGraph" in content
    finally:
        shutil.rmtree(base_dir)


@patch("memory.summary_generator._call_local_llm")
def test_generate_weekly_summary(mock_llm):
    base_dir = tempfile.mkdtemp()
    try:
        summaries_dir = os.path.join(base_dir, "summaries", "daily")
        os.makedirs(summaries_dir)
        with open(os.path.join(summaries_dir, "2026-06-23.md"), "w") as f:
            f.write("# 2026-06-23 每日总结\n学习了Python")
        with open(os.path.join(summaries_dir, "2026-06-24.md"), "w") as f:
            f.write("# 2026-06-24 每日总结\n编写了文档")

        mock_llm.return_value = "# 第26周总结\n学习和工作并行"

        gen = SummaryGenerator(base_dir)
        path = gen.generate_weekly(2026, 26)

        assert os.path.exists(path)
    finally:
        shutil.rmtree(base_dir)


def test_generate_daily_no_index_returns_none():
    base_dir = tempfile.mkdtemp()
    try:
        gen = SummaryGenerator(base_dir)
        path = gen.generate_daily("2026-01-01")
        assert path is None
    finally:
        shutil.rmtree(base_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_summary_generator.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement summary generator**

```python
# memory/summary_generator.py
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import requests


def _call_local_llm(
    prompt: str,
    base_url: str = "http://localhost:11434",
    model: str = "qwen2.5:7b",
) -> str:
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception:
        return ""


class SummaryGenerator:
    def __init__(
        self,
        base_dir: str,
        llm_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen2.5:7b",
    ):
        self._base_dir = Path(base_dir)
        self._llm_base_url = llm_base_url
        self._llm_model = llm_model

    def generate_daily(self, date: str) -> str | None:
        index_path = self._base_dir / "index" / f"{date}.md"
        if not index_path.exists():
            return None

        index_content = index_path.read_text(encoding="utf-8")
        prompt = (
            f"以下是用户{date}的活动记录索引：\n\n"
            f"{index_content}\n\n"
            f"请生成一份当日总结，按「学习」「工作」分类，"
            f"最后附上时间统计。格式参考：\n"
            f"# {date} 每日总结\n## 学习\n- ...\n## 工作\n- ...\n## 统计\n- ...\n"
        )

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model)
        if not summary:
            summary = f"# {date} 每日总结\n\n{index_content}"

        output_dir = self._base_dir / "summaries" / "daily"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{date}.md"
        output_path.write_text(summary, encoding="utf-8")
        return str(output_path)

    def generate_weekly(self, year: int, week: int) -> str | None:
        daily_dir = self._base_dir / "summaries" / "daily"
        if not daily_dir.exists():
            return None

        daily_contents = []
        for f in sorted(daily_dir.glob("*.md")):
            try:
                d = datetime.strptime(f.stem, "%Y-%m-%d")
                iso_year, iso_week, _ = d.isocalendar()
                if iso_year == year and iso_week == week:
                    daily_contents.append(f.read_text(encoding="utf-8"))
            except ValueError:
                continue

        if not daily_contents:
            return None

        combined = "\n\n---\n\n".join(daily_contents)
        prompt = (
            f"以下是{year}年第{week}周的每日总结：\n\n"
            f"{combined}\n\n"
            f"请生成一份周总结，包含学习方向、工作产出、时间分配。\n"
        )

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model)
        if not summary:
            summary = f"# {year}年第{week}周总结\n\n{combined}"

        output_dir = self._base_dir / "summaries" / "weekly"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{year}-W{week:02d}.md"
        output_path.write_text(summary, encoding="utf-8")
        return str(output_path)

    def generate_monthly(self, year: int, month: int) -> str | None:
        weekly_dir = self._base_dir / "summaries" / "weekly"
        if not weekly_dir.exists():
            return None

        weekly_contents = []
        for f in sorted(weekly_dir.glob(f"{year}-W*.md")):
            weekly_contents.append(f.read_text(encoding="utf-8"))

        if not weekly_contents:
            return None

        combined = "\n\n---\n\n".join(weekly_contents)
        prompt = (
            f"以下是{year}年{month}月的周总结：\n\n"
            f"{combined}\n\n"
            f"请生成一份月度总结。\n"
        )

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model)
        if not summary:
            summary = f"# {year}年{month}月总结\n\n{combined}"

        output_dir = self._base_dir / "summaries" / "monthly"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{year}-{month:02d}.md"
        output_path.write_text(summary, encoding="utf-8")
        return str(output_path)

    def check_and_generate_pending(self) -> list[str]:
        generated = []
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")

        daily_path = self._base_dir / "summaries" / "daily" / f"{yesterday_str}.md"
        if not daily_path.exists():
            result = self.generate_daily(yesterday_str)
            if result:
                generated.append(result)

        if today.weekday() == 0:
            iso_year, iso_week, _ = yesterday.isocalendar()
            weekly_path = self._base_dir / "summaries" / "weekly" / f"{iso_year}-W{iso_week:02d}.md"
            if not weekly_path.exists():
                result = self.generate_weekly(iso_year, iso_week)
                if result:
                    generated.append(result)

        if today.day == 1:
            result = self.generate_monthly(yesterday.year, yesterday.month)
            if result:
                generated.append(result)

        return generated
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_summary_generator.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add memory/summary_generator.py tests/test_summary_generator.py
git commit -m "feat: three-tier summary generator (daily/weekly/monthly)"
```

---

### Task 8: Hermes Launcher + Client

**Files:**
- Create: `app/hermes_launcher.py`
- Create: `app/hermes_client.py`
- Create: `tests/test_hermes_launcher.py`
- Create: `tests/test_hermes_client.py`

**Interfaces:**
- Consumes: nothing
- Produces: `app.hermes_launcher.HermesLauncher` class with methods:
  - `start() -> bool` — launches Hermes gateway, returns True if successful
  - `stop() -> None` — stops the Hermes process
  - `is_healthy() -> bool` — checks gateway health
  - `ensure_running() -> bool` — restarts if needed
- Produces: `app.hermes_client.HermesClient` class with methods:
  - `send_message(text: str) -> str` — sends message to Hermes, returns response
  - `is_connected() -> bool` — checks connection status

- [ ] **Step 1: Write failing tests**

```python
# tests/test_hermes_launcher.py
from unittest.mock import patch, MagicMock
from app.hermes_launcher import HermesLauncher


@patch("shutil.which")
def test_hermes_not_installed(mock_which):
    mock_which.return_value = None
    launcher = HermesLauncher()
    assert launcher.is_installed() is False


@patch("shutil.which")
def test_hermes_installed(mock_which):
    mock_which.return_value = "/usr/local/bin/hermes"
    launcher = HermesLauncher()
    assert launcher.is_installed() is True


@patch("requests.get")
def test_health_check_healthy(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    launcher = HermesLauncher()
    assert launcher.is_healthy() is True


@patch("requests.get")
def test_health_check_unhealthy(mock_get):
    mock_get.side_effect = ConnectionError()
    launcher = HermesLauncher()
    assert launcher.is_healthy() is False
```

```python
# tests/test_hermes_client.py
from unittest.mock import patch, MagicMock
from app.hermes_client import HermesClient


@patch("requests.post")
def test_send_message_success(mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"response": "今天你阅读了2篇技术文章。"},
    )
    client = HermesClient(base_url="http://localhost:3000")
    response = client.send_message("今天做了什么？")
    assert "技术文章" in response


@patch("requests.post")
def test_send_message_failure(mock_post):
    mock_post.side_effect = ConnectionError()
    client = HermesClient(base_url="http://localhost:3000")
    response = client.send_message("测试")
    assert response is None


@patch("requests.get")
def test_is_connected_true(mock_get):
    mock_get.return_value = MagicMock(status_code=200)
    client = HermesClient(base_url="http://localhost:3000")
    assert client.is_connected() is True


@patch("requests.get")
def test_is_connected_false(mock_get):
    mock_get.side_effect = ConnectionError()
    client = HermesClient(base_url="http://localhost:3000")
    assert client.is_connected() is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_hermes_launcher.py tests/test_hermes_client.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement launcher and client**

```python
# app/hermes_launcher.py
from __future__ import annotations

import logging
import shutil
import subprocess
import time

import requests

logger = logging.getLogger(__name__)

HEALTH_URL = "http://localhost:3000/health"


class HermesLauncher:
    def __init__(self, gateway_port: int = 3000):
        self._port = gateway_port
        self._process: subprocess.Popen | None = None
        self._health_url = f"http://localhost:{gateway_port}/health"

    def is_installed(self) -> bool:
        return shutil.which("hermes") is not None

    def start(self) -> bool:
        if not self.is_installed():
            logger.error("Hermes is not installed")
            return False

        if self.is_healthy():
            logger.info("Hermes gateway already running")
            return True

        try:
            self._process = subprocess.Popen(
                ["hermes", "gateway", "start"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(30):
                time.sleep(1)
                if self.is_healthy():
                    logger.info("Hermes gateway started successfully")
                    return True
            logger.error("Hermes gateway failed to start within 30s")
            return False
        except Exception:
            logger.exception("Failed to start Hermes gateway")
            return False

    def stop(self) -> None:
        if self._process:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

    def is_healthy(self) -> bool:
        try:
            resp = requests.get(self._health_url, timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def ensure_running(self) -> bool:
        if self.is_healthy():
            return True
        logger.warning("Hermes gateway not healthy, attempting restart")
        self.stop()
        return self.start()
```

```python
# app/hermes_client.py
from __future__ import annotations

import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class HermesClient:
    def __init__(self, base_url: str = "http://localhost:3000"):
        self._base_url = base_url

    def send_message(self, text: str) -> Optional[str]:
        try:
            resp = requests.post(
                f"{self._base_url}/api/chat",
                json={"message": text},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception:
            logger.exception("Failed to send message to Hermes")
            return None

    def is_connected(self) -> bool:
        try:
            resp = requests.get(f"{self._base_url}/health", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_hermes_launcher.py tests/test_hermes_client.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/hermes_launcher.py app/hermes_client.py tests/test_hermes_launcher.py tests/test_hermes_client.py
git commit -m "feat: Hermes gateway launcher and HTTP client"
```

---

### Task 9: MCP Server (Custom Tools for Hermes)

**Files:**
- Create: `app/mcp_server.py`
- Create: `tests/test_mcp_server.py`

**Interfaces:**
- Consumes: Memory files from Task 4, Task 7
- Produces: `app.mcp_server.PetMcpServer` class with methods:
  - `start(port: int) -> None` — starts MCP server in background
  - `stop() -> None`
- Produces MCP tools: `read_activity_index`, `read_activity_detail`, `read_summary`, `list_available_dates`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_mcp_server.py
import os
import tempfile
import shutil
from app.mcp_server import (
    handle_read_activity_index,
    handle_read_activity_detail,
    handle_read_summary,
    handle_list_available_dates,
)


def test_read_activity_index():
    base_dir = tempfile.mkdtemp()
    try:
        index_dir = os.path.join(base_dir, "index")
        os.makedirs(index_dir)
        with open(os.path.join(index_dir, "2026-06-25.md"), "w", encoding="utf-8") as f:
            f.write("# 2026-06-25 活动索引\n\n- [10:00] 阅读了文章\n")

        result = handle_read_activity_index(base_dir, "2026-06-25")
        assert "阅读了文章" in result
    finally:
        shutil.rmtree(base_dir)


def test_read_activity_index_today():
    base_dir = tempfile.mkdtemp()
    try:
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        index_dir = os.path.join(base_dir, "index")
        os.makedirs(index_dir)
        with open(os.path.join(index_dir, f"{today}.md"), "w", encoding="utf-8") as f:
            f.write("# Today\n- activity\n")

        result = handle_read_activity_index(base_dir, "today")
        assert "activity" in result
    finally:
        shutil.rmtree(base_dir)


def test_read_activity_detail():
    base_dir = tempfile.mkdtemp()
    try:
        activity_dir = os.path.join(base_dir, "activities", "2026-06-25")
        os.makedirs(activity_dir)
        with open(os.path.join(activity_dir, "activity_001.md"), "w", encoding="utf-8") as f:
            f.write("时间：2026-06-25 10:00-10:35\n详细内容")

        result = handle_read_activity_detail(
            base_dir, "activities/2026-06-25/activity_001.md",
        )
        assert "详细内容" in result
    finally:
        shutil.rmtree(base_dir)


def test_read_summary():
    base_dir = tempfile.mkdtemp()
    try:
        daily_dir = os.path.join(base_dir, "summaries", "daily")
        os.makedirs(daily_dir)
        with open(os.path.join(daily_dir, "2026-06-25.md"), "w", encoding="utf-8") as f:
            f.write("# 每日总结\n学习了很多")

        result = handle_read_summary(base_dir, "daily", "2026-06-25")
        assert "学习了很多" in result
    finally:
        shutil.rmtree(base_dir)


def test_list_available_dates():
    base_dir = tempfile.mkdtemp()
    try:
        index_dir = os.path.join(base_dir, "index")
        os.makedirs(index_dir)
        with open(os.path.join(index_dir, "2026-06-25.md"), "w") as f:
            f.write("- item1\n- item2\n")
        with open(os.path.join(index_dir, "2026-06-24.md"), "w") as f:
            f.write("- item1\n")

        result = handle_list_available_dates(base_dir)
        assert len(result) == 2
        assert result["2026-06-25"] == 2
        assert result["2026-06-24"] == 1
    finally:
        shutil.rmtree(base_dir)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_mcp_server.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement MCP server**

```python
# app/mcp_server.py
from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path


def handle_read_activity_index(base_dir: str, date: str) -> str:
    if date == "today":
        date = datetime.now().strftime("%Y-%m-%d")

    index_path = Path(base_dir) / "index" / f"{date}.md"
    if not index_path.exists():
        return f"没有找到 {date} 的活动记录。"
    return index_path.read_text(encoding="utf-8")


def handle_read_activity_detail(base_dir: str, file_path: str) -> str:
    full_path = Path(base_dir) / file_path
    if not full_path.exists():
        return f"文件不存在：{file_path}"
    return full_path.read_text(encoding="utf-8")


def handle_read_summary(base_dir: str, summary_type: str, key: str) -> str:
    path = Path(base_dir) / "summaries" / summary_type / f"{key}.md"
    if not path.exists():
        return f"没有找到 {summary_type} 类型的 {key} 总结。"
    return path.read_text(encoding="utf-8")


def handle_list_available_dates(base_dir: str, date_range: str | None = None) -> dict[str, int]:
    index_dir = Path(base_dir) / "index"
    if not index_dir.exists():
        return {}

    result = {}
    for f in sorted(index_dir.glob("*.md")):
        date = f.stem
        content = f.read_text(encoding="utf-8")
        count = len([line for line in content.split("\n") if line.strip().startswith("- [")])
        result[date] = count
    return result


class PetMcpServer:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        self._thread = None

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "read_activity_index",
                "description": "读取某天的活动索引，获取当天所有活动的一句话摘要列表",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "日期，如2026-06-25或today"},
                    },
                    "required": ["date"],
                },
            },
            {
                "name": "read_activity_detail",
                "description": "读取某条活动的完整记忆文档",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "记忆文档路径"},
                    },
                    "required": ["file_path"],
                },
            },
            {
                "name": "read_summary",
                "description": "读取每日/周/月总结文档",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                        "key": {"type": "string", "description": "标识，如2026-06-25或2026-W26"},
                    },
                    "required": ["type", "key"],
                },
            },
            {
                "name": "list_available_dates",
                "description": "列出有活动记录的日期列表和每天的活动条数",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "range": {"type": "string", "description": "可选，如this_week"},
                    },
                },
            },
        ]

    def handle_call(self, tool_name: str, arguments: dict) -> str:
        if tool_name == "read_activity_index":
            return handle_read_activity_index(self._base_dir, arguments["date"])
        elif tool_name == "read_activity_detail":
            return handle_read_activity_detail(self._base_dir, arguments["file_path"])
        elif tool_name == "read_summary":
            return handle_read_summary(self._base_dir, arguments["type"], arguments["key"])
        elif tool_name == "list_available_dates":
            dates = handle_list_available_dates(self._base_dir, arguments.get("range"))
            lines = [f"{d}: {c}条活动" for d, c in dates.items()]
            return "\n".join(lines) if lines else "暂无活动记录"
        return f"未知工具：{tool_name}"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mcp_server.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add app/mcp_server.py tests/test_mcp_server.py
git commit -m "feat: MCP server with activity memory tools for Hermes"
```

---

### Task 10: PyQt6 UI (Main Window + Chat + Status Bar)

**Files:**
- Create: `ui/main_window.py`
- Create: `ui/chat_widget.py`
- Create: `ui/status_bar.py`
- Create: `tests/test_ui.py`

**Interfaces:**
- Consumes: `app.hermes_client.HermesClient` from Task 8
- Produces: `ui.main_window.MainWindow(QMainWindow)` class
- Produces: `ui.chat_widget.ChatWidget(QWidget)` with signal `message_sent(str)` and slot `append_response(str)`
- Produces: `ui.status_bar.StatusBar(QWidget)` with methods `set_hermes_status(bool)`, `set_monitor_status(bool)`

- [ ] **Step 1: Write failing test (smoke test — no display needed)**

```python
# tests/test_ui.py
import sys
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_chat_widget_creation(qapp):
    from ui.chat_widget import ChatWidget
    widget = ChatWidget()
    assert widget is not None
    widget.append_message("user", "Hello")
    widget.append_message("assistant", "Hi there")


def test_status_bar_creation(qapp):
    from ui.status_bar import StatusBar
    bar = StatusBar()
    bar.set_hermes_status(True)
    bar.set_monitor_status(True)
    bar.set_hermes_status(False)


def test_main_window_creation(qapp):
    from ui.main_window import MainWindow
    window = MainWindow.__new__(MainWindow)
    assert window is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_ui.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement UI components**

```python
# ui/chat_widget.py
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton,
)
from PyQt6.QtCore import pyqtSignal, Qt


class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            "QTextEdit { background-color: #f5f5f5; border: 1px solid #ddd; "
            "border-radius: 8px; padding: 8px; font-size: 14px; }"
        )
        layout.addWidget(self._chat_display, stretch=1)

        input_layout = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入消息...")
        self._input_field.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 6px; "
            "padding: 8px; font-size: 14px; }"
        )
        self._input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input_field, stretch=1)

        self._send_button = QPushButton("发送")
        self._send_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self._send_button.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_button)

        layout.addLayout(input_layout)

    def _on_send(self):
        text = self._input_field.text().strip()
        if text:
            self.append_message("user", text)
            self._input_field.clear()
            self.message_sent.emit(text)

    def append_message(self, role: str, content: str):
        if role == "user":
            self._chat_display.append(
                f'<div style="text-align:right; margin:4px 0;">'
                f'<span style="background-color:#DCF8C6; padding:6px 10px; '
                f'border-radius:8px; display:inline-block;">{content}</span></div>'
            )
        else:
            self._chat_display.append(
                f'<div style="text-align:left; margin:4px 0;">'
                f'<span style="background-color:#FFFFFF; padding:6px 10px; '
                f'border-radius:8px; border:1px solid #eee; display:inline-block;">'
                f'{content}</span></div>'
            )

    def set_input_enabled(self, enabled: bool):
        self._input_field.setEnabled(enabled)
        self._send_button.setEnabled(enabled)
```

```python
# ui/status_bar.py
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt


class StatusBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)

        self._hermes_label = QLabel()
        self._monitor_label = QLabel()

        layout.addWidget(self._monitor_label)
        layout.addStretch()
        layout.addWidget(self._hermes_label)

        self.set_hermes_status(False)
        self.set_monitor_status(False)

    def set_hermes_status(self, connected: bool):
        if connected:
            self._hermes_label.setText("Agent: 已连接")
            self._hermes_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self._hermes_label.setText("Agent: 未连接")
            self._hermes_label.setStyleSheet("color: red; font-size: 12px;")

    def set_monitor_status(self, running: bool):
        if running:
            self._monitor_label.setText("监控: 运行中")
            self._monitor_label.setStyleSheet("color: green; font-size: 12px;")
        else:
            self._monitor_label.setText("监控: 已停止")
            self._monitor_label.setStyleSheet("color: gray; font-size: 12px;")
```

```python
# ui/main_window.py
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt

from ui.chat_widget import ChatWidget
from ui.status_bar import StatusBar


class MainWindow(QMainWindow):
    def __init__(
        self,
        on_message_sent=None,
        width: int = 400,
        height: int = 600,
    ):
        super().__init__()
        self.setWindowTitle("逗叽脑袋 - 桌面宠物 Agent")
        self.setFixedSize(width, height)
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.chat_widget = ChatWidget()
        layout.addWidget(self.chat_widget, stretch=1)

        self.status_bar = StatusBar()
        layout.addWidget(self.status_bar)

        if on_message_sent:
            self.chat_widget.message_sent.connect(on_message_sent)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_ui.py -v`
Expected: All 3 tests PASS (may need `QT_QPA_PLATFORM=offscreen` on headless systems)

- [ ] **Step 5: Commit**

```bash
git add ui/ tests/test_ui.py
git commit -m "feat: PyQt6 UI with chat widget and status bar"
```

---

### Task 11: Application Entry Point (Orchestration)

**Files:**
- Create: `app/main.py`
- Modify: `tests/test_config.py` — add `_config_instance` reset in setup

**Interfaces:**
- Consumes: All previous tasks
- Produces: `app.main.main() -> None` — entry point that starts the application

- [ ] **Step 1: Write failing test**

```python
# tests/test_app_main.py
from unittest.mock import patch, MagicMock


@patch("app.main.QApplication")
@patch("app.main.HermesLauncher")
@patch("app.main.ScreenMonitor")
@patch("app.main.MainWindow")
@patch("app.main.SummaryGenerator")
def test_app_startup_sequence(
    mock_summary_gen, mock_window, mock_monitor, mock_launcher, mock_qapp,
):
    mock_launcher_instance = MagicMock()
    mock_launcher_instance.is_installed.return_value = True
    mock_launcher_instance.start.return_value = True
    mock_launcher_instance.is_healthy.return_value = True
    mock_launcher.return_value = mock_launcher_instance

    mock_monitor_instance = MagicMock()
    mock_monitor.return_value = mock_monitor_instance

    mock_window_instance = MagicMock()
    mock_window.return_value = mock_window_instance

    mock_qapp_instance = MagicMock()
    mock_qapp.return_value = mock_qapp_instance
    mock_qapp_instance.exec.return_value = 0

    from app.main import PetApp
    app = PetApp.__new__(PetApp)
    app._config = {
        "monitor": {"enabled": True, "interval_seconds": 30, "idle_timeout_seconds": 120,
                     "confirm_count": 2},
        "screenshots": {"quality": 75},
        "memory": {"base_dir": "/tmp/test-pet-memory"},
        "llm": {"local": {"base_url": "http://localhost:11434", "model": "qwen2.5:7b"}},
        "ui": {"window_width": 400, "window_height": 600},
    }
    app._launcher = mock_launcher_instance
    app._monitor = mock_monitor_instance
    app._summary_gen = MagicMock()

    app._start_services()

    mock_launcher_instance.start.assert_called_once()
    mock_monitor_instance.start.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_app_main.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement application entry point**

```python
# app/main.py
from __future__ import annotations

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from app.config import load_config, get_config
from app.hermes_launcher import HermesLauncher
from app.hermes_client import HermesClient
from monitor.screen_monitor import ScreenMonitor
from memory.summary_generator import SummaryGenerator
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)


class PetApp:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        self._config = load_config(config_path)

        memory_dir = self._config["memory"]["base_dir"]
        os.makedirs(memory_dir, exist_ok=True)

        self._launcher = HermesLauncher()
        self._client = HermesClient()
        self._monitor = ScreenMonitor(
            base_dir=memory_dir,
            interval=self._config["monitor"]["interval_seconds"],
            idle_timeout=self._config["monitor"]["idle_timeout_seconds"],
            confirm_count=self._config["monitor"]["confirm_count"],
            screenshot_quality=self._config["screenshots"]["quality"],
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._summary_gen = SummaryGenerator(
            base_dir=memory_dir,
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._window: MainWindow | None = None
        self._health_timer: QTimer | None = None

    def run(self):
        app = QApplication(sys.argv)

        self._window = MainWindow(
            on_message_sent=self._on_user_message,
            width=self._config["ui"]["window_width"],
            height=self._config["ui"]["window_height"],
        )

        self._start_services()
        self._window.show()

        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(30000)

        exit_code = app.exec()

        self._shutdown()
        sys.exit(exit_code)

    def _start_services(self):
        if self._launcher.is_installed():
            success = self._launcher.start()
            if self._window:
                self._window.status_bar.set_hermes_status(success)
                if not success:
                    self._window.chat_widget.append_message(
                        "system", "Agent 服务启动失败，对话功能暂时不可用。"
                    )
        else:
            if self._window:
                self._window.status_bar.set_hermes_status(False)
                self._window.chat_widget.append_message(
                    "system", "未检测到 Hermes Agent，请先安装。"
                )

        if self._config["monitor"]["enabled"]:
            self._monitor.start()
            if self._window:
                self._window.status_bar.set_monitor_status(True)

        self._summary_gen.check_and_generate_pending()

    def _on_user_message(self, text: str):
        if not self._client.is_connected():
            if self._window:
                self._window.chat_widget.append_message(
                    "system", "Agent 服务异常，对话功能暂时不可用。"
                )
            return

        if self._window:
            self._window.chat_widget.set_input_enabled(False)

        response = self._client.send_message(text)

        if self._window:
            if response:
                self._window.chat_widget.append_message("assistant", response)
            else:
                self._window.chat_widget.append_message(
                    "system", "获取回复失败，请稍后重试。"
                )
            self._window.chat_widget.set_input_enabled(True)

    def _check_health(self):
        hermes_ok = self._launcher.is_healthy()
        monitor_ok = self._monitor.is_running()

        if self._window:
            self._window.status_bar.set_hermes_status(hermes_ok)
            self._window.status_bar.set_monitor_status(monitor_ok)

        if not hermes_ok:
            self._launcher.ensure_running()

    def _shutdown(self):
        logger.info("Shutting down...")
        self._monitor.stop()

        today = __import__("datetime").datetime.now().strftime("%Y-%m-%d")
        self._summary_gen.generate_daily(today)

        from memory.screenshot_cleaner import cleanup_similar, cleanup_expired
        memory_dir = self._config["memory"]["base_dir"]
        cleanup_similar(memory_dir, today, self._config["screenshots"]["cleanup_similarity"])
        cleanup_expired(memory_dir, self._config["screenshots"]["retention_days"])

        logger.info("Shutdown complete")


def main():
    app = PetApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_app_main.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_app_main.py
git commit -m "feat: application entry point with full lifecycle management"
```

---

### Task 12: Integration Test + README

**Files:**
- Create: `tests/test_integration.py`
- Create: `README.md`

**Interfaces:**
- Consumes: All previous tasks
- Produces: End-to-end test of the monitor → memory → retrieval pipeline

- [ ] **Step 1: Write integration test**

```python
# tests/test_integration.py
"""Integration test: monitor pipeline → memory write → tool retrieval.

Mocks Windows APIs and LLM, tests the full data flow.
"""
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from PIL import Image

from monitor.scene_classifier import SceneResult


def test_full_pipeline_monitor_to_retrieval():
    base_dir = tempfile.mkdtemp()
    try:
        with (
            patch("monitor.screen_monitor.capture_foreground_window") as mock_capture,
            patch("monitor.screen_monitor.is_user_idle") as mock_idle,
            patch("monitor.screen_monitor.recognize_text") as mock_ocr,
            patch("monitor.screen_monitor.classify_scene") as mock_classify,
            patch("monitor.screen_monitor.generate_summary") as mock_summary,
        ):
            mock_idle.return_value = False
            mock_capture.return_value = (
                Image.new("RGB", (800, 600), color="white"),
                "Python异步编程指南 - Chrome",
                "Google Chrome",
            )
            mock_ocr.return_value = "Python asyncio 是标准库中用于编写异步代码的模块。" * 5
            mock_classify.return_value = SceneResult(
                scene_type="reading",
                title="Python异步编程指南",
                app_name="Google Chrome",
            )
            mock_summary.return_value = (
                "阅读了Python异步编程指南",
                "用户在Chrome中阅读了关于Python asyncio的技术文章。",
            )

            from monitor.screen_monitor import ScreenMonitor
            monitor = ScreenMonitor(
                base_dir=base_dir, interval=1, idle_timeout=120,
                confirm_count=2, screenshot_quality=75,
            )
            monitor._tick()  # first: pending
            monitor._tick()  # second: confirmed, writes activity

        from app.mcp_server import handle_read_activity_index, handle_list_available_dates
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        dates = handle_list_available_dates(base_dir)
        assert today in dates
        assert dates[today] >= 1

        index_content = handle_read_activity_index(base_dir, "today")
        assert "Python异步编程指南" in index_content

        activity_dir = os.path.join(base_dir, "activities", today)
        assert os.path.exists(activity_dir)
        activity_files = os.listdir(activity_dir)
        assert len(activity_files) >= 1

    finally:
        shutil.rmtree(base_dir)
```

- [ ] **Step 2: Run integration test**

Run: `python -m pytest tests/test_integration.py -v`
Expected: PASS

- [ ] **Step 3: Write README**

```markdown
# 逗叽脑袋 (doujianaodai)

桌面宠物 Agent — 基于 Hermes Agent 的被动屏幕监控助手。

## 功能

- **被动屏幕监控** — 自动截取前台窗口、OCR 识别内容、理解你在做什么
- **活动记忆** — 以 Markdown 文档记录你的阅读和写作活动
- **三层记忆** — 单条活动 → 每日总结 → 周/月总结
- **对话问答** — 通过 Hermes Agent 回答"今天做了什么"等问题
- **Hermes Agent 能力** — Skills、Tools、MCP、Memory 全套 Agent 能力

## 前置条件

- Windows 10+
- Python 3.11+
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [Ollama](https://ollama.ai) + Qwen2.5-7B 模型

## 安装

```bash
pip install -e .
```

## 使用

```bash
doujianaodai
```

## 配置

编辑 `config.yaml` 修改截图间隔、OCR 语言、LLM 模型等参数。

## 开发

```bash
pip install -e ".[dev]"
pytest
```
```

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_integration.py README.md
git commit -m "feat: integration test and README"
```
