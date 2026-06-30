# monitor/llm_client.py
from __future__ import annotations

import re

import requests


def _strip_think_tags(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _dedupe_ocr_texts(texts: list[str], max_chars: int = 3000) -> str:
    seen = set()
    unique = []
    for t in texts:
        t_stripped = t.strip()
        if t_stripped and t_stripped not in seen:
            seen.add(t_stripped)
            unique.append(t_stripped)
    merged = "\n---\n".join(unique)
    return merged[:max_chars]


def generate_summary(
    ocr_texts: list[str],
    window_title: str,
    scene_type: str,
    duration_sec: float = 0,
    base_url: str = "http://localhost:11434",
    model: str = "qwen3:8b",
) -> tuple[str, str]:
    scene_label = "阅读文章/文档" if scene_type == "reading" else "编写文档"

    system_prompt = (
        "你是一个屏幕活动记录助手。你的任务是根据用户屏幕截图的OCR文字内容，"
        "准确记录用户当前正在做什么以及文档/文章的核心内容。\n"
        "要求：\n"
        "- 摘要要具体，提取实际的文章标题、代码项目名、文档主题等关键信息\n"
        "- 内容要点必须提取文档中的关键概念、论点、数据、结论等实质性内容\n"
        "- 不要编造内容，只基于OCR文字推断\n"
        "- 如果OCR文字质量差或无法判断，如实说明\n"
        "- 直接输出结果，不要输出思考过程\n"
        "- 严格按照指定格式输出"
    )

    merged_ocr = _dedupe_ocr_texts(ocr_texts)
    duration_min = int(duration_sec // 60)

    prompt = (
        f"用户正在{scene_label}，持续了约{duration_min}分钟。\n"
        f"窗口标题：{window_title}\n"
        f"页面内容（多次OCR识别合并）：\n{merged_ocr}\n\n"
        f"请生成三部分内容：\n"
        f"1. 一句话摘要（20字以内，说明用户在做什么）\n"
        f"2. 内容要点（提取文档/文章中的核心内容，列出3-5个要点，每个要点一行）\n"
        f"3. 详细描述（100-200字，描述用户在做什么，文档主题是什么，"
        f"涉及哪些关键概念或技术点）\n\n"
        f"格式：\n"
        f"摘要：...\n"
        f"要点：\n- ...\n- ...\n- ...\n"
        f"详细：..."
    )

    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "system": system_prompt, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")
        text = _strip_think_tags(text)

        summary = ""
        key_points = []
        detail = ""
        current_section = None

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("摘要：") or stripped.startswith("摘要:"):
                summary = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
                current_section = None
            elif stripped.startswith("要点：") or stripped.startswith("要点:"):
                current_section = "points"
            elif stripped.startswith("详细：") or stripped.startswith("详细:"):
                detail = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
                current_section = "detail"
            elif current_section == "points" and stripped.startswith("- "):
                key_points.append(stripped)
            elif current_section == "detail" and stripped:
                detail += stripped

        if not summary:
            if text.strip():
                lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
                summary = lines[0][:50] if lines else f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"
            else:
                summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"

        content_parts = []
        if key_points:
            content_parts.append("### 内容要点\n")
            content_parts.append("\n".join(key_points))
        if detail:
            content_parts.append("\n\n### 详细描述\n")
            content_parts.append(detail)

        if not content_parts and text.strip():
            content_parts.append("### 详细描述\n")
            content_parts.append(text.strip()[:500])

        full_content = "\n".join(content_parts) if content_parts else f"用户在{window_title}中进行了{scene_label}活动。"

        return summary, full_content
    except Exception:
        summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"
        full_content = f"用户在{window_title}中进行了{scene_label}活动。"
        return summary, full_content
