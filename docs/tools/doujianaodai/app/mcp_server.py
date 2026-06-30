"""MCP tool handlers — shared between pet_mcp_server.py and internal tests.

All handlers read from the shared memory directory.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path


def handle_read_activity_index(base_dir: str, date: str) -> str:
    if date == "today":
        date = datetime.now().strftime("%Y-%m-%d")
    path = Path(base_dir) / "index" / f"{date}.md"
    if not path.exists():
        return f"没有找到 {date} 的活动记录。"
    return path.read_text(encoding="utf-8")


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
        content = f.read_text(encoding="utf-8")
        count = len([l for l in content.split("\n") if l.strip().startswith("- ")])
        result[f.stem] = count
    return result
