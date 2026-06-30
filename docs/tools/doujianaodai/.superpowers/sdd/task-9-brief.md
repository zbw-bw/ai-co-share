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

