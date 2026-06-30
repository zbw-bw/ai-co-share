# app/stream_parser.py
from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class StreamEvent:
    event_type: str      # "thinking" | "text" | "tool_use" | "tool_result" | "status" | "done"
    content: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"event_type": self.event_type, "content": self.content, "metadata": self.metadata}


def parse_stream_event(line: str) -> StreamEvent | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None

    msg_type = data.get("type")

    if msg_type == "system" and data.get("subtype") == "init":
        model = data.get("model", "unknown")
        return StreamEvent(event_type="status", content=f"已连接 {model}", metadata={"model": model})

    if msg_type == "assistant":
        message = data.get("message", data)
        contents = message.get("content", [])
        for item in contents:
            item_type = item.get("type")
            if item_type == "thinking":
                return StreamEvent(event_type="thinking", content=item.get("thinking", ""))
            if item_type == "text":
                return StreamEvent(event_type="text", content=item.get("text", ""))
            if item_type == "tool_use":
                name = item.get("name", "")
                return StreamEvent(
                    event_type="tool_use",
                    content=name,
                    metadata={"input": item.get("input", {})},
                )
            if item_type == "tool_result":
                result_content = item.get("content", "")
                if isinstance(result_content, list):
                    result_content = " ".join(
                        part.get("text", "") for part in result_content if isinstance(part, dict)
                    )
                return StreamEvent(event_type="tool_result", content=str(result_content))
        return None

    if msg_type == "result":
        usage = data.get("usage", {})
        return StreamEvent(
            event_type="done",
            content=data.get("result", ""),
            metadata={
                "session_id": data.get("session_id", ""),
                "duration_ms": data.get("duration_ms", 0),
                "total_cost_usd": data.get("total_cost_usd", 0),
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
            },
        )

    return None
