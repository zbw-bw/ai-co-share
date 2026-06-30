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
