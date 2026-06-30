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
