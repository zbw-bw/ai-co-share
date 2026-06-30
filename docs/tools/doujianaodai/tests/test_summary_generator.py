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
