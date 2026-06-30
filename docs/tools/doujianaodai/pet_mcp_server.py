#!/usr/bin/env python3
"""Pet Memory MCP Server — standalone stdio server for Claude Code.

Exposes activity memory tools so Claude Code can query what the user did.
Reads from the shared memory directory (~/.pet-memory/).

Memory reading follows a layered strategy:
  Layer 1: Index (one-line summaries per day) — cheapest
  Layer 2: Activity detail (key points + detailed description, NO OCR raw text)
  Layer 3: Raw OCR text — only when explicitly requested for deep inspection
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

MEMORY_DIR = os.path.expanduser("~/.pet-memory")


def _strip_ocr_section(text: str) -> str:
    """Remove the OCR原文片段 section from activity content."""
    return re.sub(r"\n*### OCR原文片段\n+```\n.*?```\n?", "", text, flags=re.DOTALL).rstrip()


def handle_read_activity_index(date: str) -> str:
    if date == "today":
        date = datetime.now().strftime("%Y-%m-%d")
    path = Path(MEMORY_DIR) / "index" / f"{date}.md"
    if not path.exists():
        return f"没有找到 {date} 的活动记录。"
    return path.read_text(encoding="utf-8")


def handle_read_activity_detail(file_path: str) -> str:
    """Read activity detail — returns key points + description, excludes OCR raw text."""
    full_path = Path(MEMORY_DIR) / file_path
    if not full_path.exists():
        return f"文件不存在：{file_path}"
    content = full_path.read_text(encoding="utf-8")
    return _strip_ocr_section(content)


def handle_read_activity_raw(file_path: str) -> str:
    """Read the OCR raw text section only — use when summary lacks needed detail."""
    full_path = Path(MEMORY_DIR) / file_path
    if not full_path.exists():
        return f"文件不存在：{file_path}"
    content = full_path.read_text(encoding="utf-8")
    match = re.search(r"### OCR原文片段\n+```\n(.*?)```", content, flags=re.DOTALL)
    if match:
        return match.group(1).strip()
    return "该活动没有保存OCR原文。"


def handle_read_summary(summary_type: str, key: str) -> str:
    path = Path(MEMORY_DIR) / "summaries" / summary_type / f"{key}.md"
    if not path.exists():
        return f"没有找到 {summary_type} 类型的 {key} 总结。"
    return path.read_text(encoding="utf-8")


def handle_list_available_dates(date_range: str | None = None) -> str:
    index_dir = Path(MEMORY_DIR) / "index"
    if not index_dir.exists():
        return "暂无活动记录"
    result = []
    for f in sorted(index_dir.glob("*.md")):
        content = f.read_text(encoding="utf-8")
        count = len([l for l in content.split("\n") if l.strip().startswith("- ")])
        result.append(f"{f.stem}: {count}条活动")
    return "\n".join(result) if result else "暂无活动记录"


TOOLS = [
    {
        "name": "read_activity_index",
        "description": (
            "【第1层-索引】读取某天的活动索引，每条活动一行摘要。"
            "优先使用此工具获取概览，再按需读取详情。"
            "用户问'今天做了什么'时先用这个。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "日期如'2026-06-25'，或'today'表示今天"}
            },
            "required": ["date"],
        },
    },
    {
        "name": "read_activity_detail",
        "description": (
            "【第2层-详情】读取某条活动的内容要点和详细描述（不含OCR原文）。"
            "当索引信息不够回答用户问题时使用。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文档路径如'activities/2026-06-25/activity_001.md'"}
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_activity_raw",
        "description": (
            "【第3层-原文】读取某条活动的OCR原始文字。"
            "仅当详情层信息仍不足以回答用户问题时才使用，例如用户追问文档中的具体细节。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "文档路径如'activities/2026-06-25/activity_001.md'"}
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "read_summary",
        "description": "读取每日/周/月活动总结。用户问'这周学了什么'等跨天问题时使用。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                "key": {"type": "string", "description": "如'2026-06-25'、'2026-W26'、'2026-06'"}
            },
            "required": ["type", "key"],
        },
    },
    {
        "name": "list_available_dates",
        "description": "列出有活动记录的所有日期及活动条数。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "range": {"type": "string", "description": "可选范围如'this_week'"}
            },
        },
    },
]


def handle_call(tool_name: str, arguments: dict) -> str:
    if tool_name == "read_activity_index":
        return handle_read_activity_index(arguments["date"])
    elif tool_name == "read_activity_detail":
        return handle_read_activity_detail(arguments["file_path"])
    elif tool_name == "read_activity_raw":
        return handle_read_activity_raw(arguments["file_path"])
    elif tool_name == "read_summary":
        return handle_read_summary(arguments["type"], arguments["key"])
    elif tool_name == "list_available_dates":
        return handle_list_available_dates(arguments.get("range"))
    return f"未知工具：{tool_name}"


def send_response(response: dict):
    msg = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(msg.encode())}\r\n\r\n{msg}")
    sys.stdout.flush()


def read_message() -> dict | None:
    header = ""
    while True:
        ch = sys.stdin.read(1)
        if not ch:
            return None
        header += ch
        if header.endswith("\r\n\r\n"):
            break
    length = int(header.split("Content-Length: ")[1].split("\r\n")[0])
    body = sys.stdin.read(length)
    return json.loads(body)


def main():
    os.makedirs(MEMORY_DIR, exist_ok=True)

    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "pet-memory", "version": "0.1.0"},
                },
            })
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS},
            })
        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result_text = handle_call(tool_name, arguments)
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": result_text}],
                    "isError": False,
                },
            })
        elif msg_id is not None:
            send_response({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"},
            })


if __name__ == "__main__":
    main()
