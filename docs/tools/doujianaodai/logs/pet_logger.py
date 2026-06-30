from __future__ import annotations

import json
from pathlib import Path


class MonitorLogger:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)

    def _append(self, date: str, line: str):
        log_dir = self._base_dir / "logs" / "monitor"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{date}.md"
        if not log_file.exists():
            log_file.write_text(f"# {date} 监控日志\n\n", encoding="utf-8")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log_screenshot(self, date: str, time: str, app: str, title: str, ocr_len: int, ocr_engine: str = ""):
        engine_str = f" ocr_engine={ocr_engine}" if ocr_engine else ""
        self._append(date, f"- [{time}] SCREENSHOT app={app} title=\"{title}\" ocr_len={ocr_len}{engine_str}")

    def log_state_transition(self, date: str, time: str, from_state: str, to_state: str, reason: str = ""):
        reason_str = f" reason=\"{reason}\"" if reason else ""
        self._append(date, f"- [{time}] STATE {from_state} → {to_state}{reason_str}")

    def log_summary_generated(self, date: str, time: str, activity_file: str, ocr_inputs: int, llm_time: float):
        self._append(date, f"- [{time}] SUMMARY_GENERATED activity={activity_file} ocr_inputs={ocr_inputs} llm_time={llm_time:.1f}s")


class ChatLogger:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)

    def log_conversation(
        self,
        date: str,
        time: str,
        session_id: str,
        user_message: str,
        assistant_response: str,
        duration_sec: float,
        model: str = "",
    ):
        log_dir = self._base_dir / "logs" / "chat"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{date}.md"
        if not log_file.exists():
            log_file.write_text(f"# {date} 对话日志\n\n", encoding="utf-8")

        entry = (
            f"## {time} session={session_id}\n\n"
            f"**用户**: {user_message}\n\n"
            f"**助手**: {assistant_response}\n\n"
            f"- 耗时: {duration_sec:.1f}s\n"
        )
        if model:
            entry += f"- 模型: {model}\n"
        entry += "\n---\n\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)


class StatsCollector:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)
        self._reset()

    def _reset(self):
        self._screenshots = 0
        self._transitions: dict[str, int] = {}
        self._engaged_sessions = 0
        self._engaged_durations: list[float] = []
        self._browsing_sessions = 0
        self._summaries = 0
        self._llm_calls = 0
        self._llm_times: list[float] = []
        self._chat_messages = 0
        self._chat_times: list[float] = []
        self._tools_used: dict[str, int] = {}

    def record_screenshot(self):
        self._screenshots += 1

    def record_state_transition(self, from_state: str, to_state: str):
        key = f"{from_state.lower()}_to_{to_state.lower()}"
        self._transitions[key] = self._transitions.get(key, 0) + 1
        if to_state == "BROWSING":
            self._browsing_sessions += 1

    def record_engaged_session(self, duration: float):
        self._engaged_sessions += 1
        self._engaged_durations.append(duration)

    def record_summary(self):
        self._summaries += 1

    def record_llm_call(self, duration: float):
        self._llm_calls += 1
        self._llm_times.append(duration)

    def record_chat(self, response_time: float, tools: list[str] | None = None):
        self._chat_messages += 1
        self._chat_times.append(response_time)
        for t in (tools or []):
            self._tools_used[t] = self._tools_used.get(t, 0) + 1

    def flush(self, date: str):
        stats_dir = self._base_dir / "logs" / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)

        avg_engaged = (
            sum(self._engaged_durations) / len(self._engaged_durations)
            if self._engaged_durations else 0
        )
        avg_llm = (
            sum(self._llm_times) / len(self._llm_times)
            if self._llm_times else 0
        )
        avg_chat = (
            sum(self._chat_times) / len(self._chat_times)
            if self._chat_times else 0
        )

        data = {
            "date": date,
            "monitor": {
                "screenshots_total": self._screenshots,
                "state_transitions": dict(self._transitions),
                "engaged_sessions": self._engaged_sessions,
                "engaged_avg_duration_sec": round(avg_engaged, 1),
                "browsing_sessions": self._browsing_sessions,
                "summaries_generated": self._summaries,
                "llm_calls_total": self._llm_calls,
                "llm_avg_time_sec": round(avg_llm, 1),
            },
            "chat": {
                "messages_total": self._chat_messages,
                "avg_response_time_sec": round(avg_chat, 1),
                "tools_used": dict(self._tools_used),
            },
        }

        stats_file = stats_dir / f"{date}.json"
        stats_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._reset()
