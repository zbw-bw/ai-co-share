"""Bridge to Claude Code CLI — sends messages via `claude -p` subprocess.

Claude Code handles its own authentication (OAuth login). The pet app
bridges the chat UI to Claude Code. Claude Code accesses activity memory
through a shared MCP server registered in its settings.
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Generator, Optional

from logs.pet_logger import ChatLogger, StatsCollector
from app.stream_parser import StreamEvent, parse_stream_event

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(
        self,
        project_dir: str | None = None,
        chat_logger: ChatLogger | None = None,
        stats_collector: StatsCollector | None = None,
    ):
        self._project_dir = project_dir
        self._session_id: str | None = None
        self._model_override: str | None = None
        self._last_cost: dict | None = None
        self._chat_logger = chat_logger
        self._stats = stats_collector

    def send_message(self, text: str) -> Optional[str]:
        cmd = ["claude", "-p", text, "--output-format", "json"]
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=self._project_dir,
            )
            data = json.loads(result.stdout)

            if data.get("is_error"):
                error_msg = data.get("result", "Unknown error")
                logger.error("Claude Code error: %s", error_msg)
                return f"[错误] {error_msg}"

            self._session_id = data.get("session_id", self._session_id)
            response = data.get("result", "")
            duration = time.time() - start

            model = ""
            model_usage = data.get("modelUsage", {})
            if model_usage:
                model = next(iter(model_usage.keys()), "")

            self._log(text, response, duration, model)
            return response

        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out")
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude Code output: %s", e)
            return None
        except FileNotFoundError:
            logger.error("Claude Code CLI not found")
            return None
        except Exception:
            logger.exception("Failed to call Claude Code")
            return None

    def send_message_stream(self, text: str) -> Generator[StreamEvent, None, None]:
        cmd = ["claude", "-p", text, "--output-format", "stream-json", "--verbose"]
        if self._session_id:
            cmd.extend(["--resume", self._session_id])
        if self._model_override:
            cmd.extend(["--model", self._model_override])

        start = time.time()
        text_parts: list[str] = []
        model = ""

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self._project_dir,
            )
            for line in proc.stdout:
                event = parse_stream_event(line)
                if event:
                    if event.event_type == "text":
                        text_parts.append(event.content)
                    elif event.event_type == "status" and event.metadata.get("model"):
                        model = event.metadata["model"]
                    elif event.event_type == "done":
                        if event.metadata.get("session_id"):
                            self._session_id = event.metadata["session_id"]
                        self._last_cost = {
                            "total_cost_usd": event.metadata.get("total_cost_usd", 0),
                            "input_tokens": event.metadata.get("input_tokens", 0),
                            "output_tokens": event.metadata.get("output_tokens", 0),
                            "duration_ms": event.metadata.get("duration_ms", 0),
                        }
                    yield event
            proc.wait()
        except FileNotFoundError:
            logger.error("Claude Code CLI not found")
        except Exception:
            logger.exception("Stream error in Claude Code call")

        if text_parts:
            response = "".join(text_parts)
            duration = time.time() - start
            self._log(text, response, duration, model)

    def _log(self, user_msg: str, response: str, duration: float, model: str):
        now = datetime.now()
        if self._chat_logger:
            self._chat_logger.log_conversation(
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                session_id=self._session_id or "unknown",
                user_message=user_msg,
                assistant_response=response[:500],
                duration_sec=duration,
                model=model,
            )
        if self._stats:
            self._stats.record_chat(duration)

    def is_connected(self) -> bool:
        try:
            result = subprocess.run(
                ["claude", "-p", "hi", "--output-format", "json", "--max-turns", "1"],
                capture_output=True, text=True, timeout=15,
            )
            data = json.loads(result.stdout)
            return not data.get("is_error", True)
        except Exception:
            return False

    def clear_conversation(self) -> None:
        self._session_id = None
