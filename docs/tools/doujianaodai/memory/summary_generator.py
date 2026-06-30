# memory/summary_generator.py
from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import requests

SUMMARY_SYSTEM_PROMPT = (
    "你是一个用户活动总结助手。你的任务是根据用户的屏幕活动记录，"
    "生成结构化的总结报告。\n"
    "要求：\n"
    "- 按类别（学习、工作、其他）归类活动\n"
    "- 提取具体的项目名、文章标题、工具名等关键信息\n"
    "- 统计各类活动的时间占比\n"
    "- 不要编造活动记录中没有的内容\n"
    "- 直接输出结果，不要输出思考过程\n"
    "- 使用 Markdown 格式输出"
)


def _call_local_llm(
    prompt: str,
    base_url: str = "http://localhost:11434",
    model: str = "qwen3:8b",
    system: str = "",
) -> str:
    """Call local Ollama LLM and return the response text.

    Returns empty string on any error (network, timeout, bad JSON).
    """
    try:
        body = {"model": model, "prompt": prompt, "stream": False}
        if system:
            body["system"] = system
        resp = requests.post(
            f"{base_url}/api/generate",
            json=body,
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception:
        return ""


class SummaryGenerator:
    """Three-tier summary generator: daily, weekly, monthly."""

    def __init__(
        self,
        base_dir: str,
        llm_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen3:8b",
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

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model, system=SUMMARY_SYSTEM_PROMPT)
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

        daily_contents: list[str] = []
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

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model, system=SUMMARY_SYSTEM_PROMPT)
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

        weekly_contents: list[str] = []
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

        summary = _call_local_llm(prompt, self._llm_base_url, self._llm_model, system=SUMMARY_SYSTEM_PROMPT)
        if not summary:
            summary = f"# {year}年{month}月总结\n\n{combined}"

        output_dir = self._base_dir / "summaries" / "monthly"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{year}-{month:02d}.md"
        output_path.write_text(summary, encoding="utf-8")
        return str(output_path)

    def check_and_generate_pending(self) -> list[str]:
        generated: list[str] = []
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
            weekly_path = (
                self._base_dir / "summaries" / "weekly" / f"{iso_year}-W{iso_week:02d}.md"
            )
            if not weekly_path.exists():
                result = self.generate_weekly(iso_year, iso_week)
                if result:
                    generated.append(result)

        if today.day == 1:
            result = self.generate_monthly(yesterday.year, yesterday.month)
            if result:
                generated.append(result)

        return generated
