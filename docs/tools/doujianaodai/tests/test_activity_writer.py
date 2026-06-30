import os
import tempfile
import shutil
from memory.activity_writer import ActivityWriter


def test_write_activity_creates_files():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        path = writer.write_activity(
            date="2026-06-25",
            start_time="10:00",
            end_time="10:35",
            scene_type="reading",
            title="LangGraph教程",
            app_name="Chrome",
            summary="阅读了LangGraph工作流编排教程",
            content="用户在Chrome中阅读了一篇关于LangGraph工作流编排的技术文章。",
            screenshot_paths=["screenshots/2026-06-25/10-00-00.jpg"],
        )

        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "LangGraph教程" in content
        assert "10:00-10:35" in content
        assert "阅读" in content

        index_path = os.path.join(base_dir, "index", "2026-06-25.md")
        assert os.path.exists(index_path)
        with open(index_path, "r", encoding="utf-8") as f:
            index_content = f.read()
        assert "LangGraph教程" in index_content
    finally:
        shutil.rmtree(base_dir)


def test_update_activity_extends_time():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        path = writer.write_activity(
            date="2026-06-25",
            start_time="10:00",
            end_time="10:05",
            scene_type="reading",
            title="Test Article",
            app_name="Chrome",
            summary="Reading an article",
            content="Initial content.",
            screenshot_paths=[],
        )
        writer.update_activity(
            file_path=path,
            end_time="10:35",
            additional_content="More details discovered.",
            screenshot_paths=["screenshots/new.jpg"],
        )

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "10:00-10:35" in content
        assert "More details discovered" in content
        assert "screenshots/new.jpg" in content
    finally:
        shutil.rmtree(base_dir)


def test_write_multiple_activities_same_day():
    base_dir = tempfile.mkdtemp()
    try:
        writer = ActivityWriter(base_dir)
        writer.write_activity("2026-06-25", "10:00", "10:35", "reading",
                              "Article A", "Chrome", "Read A", "Content A", [])
        writer.write_activity("2026-06-25", "10:40", "11:20", "writing",
                              "Doc B", "WPS", "Wrote B", "Content B", [])

        index_path = os.path.join(base_dir, "index", "2026-06-25.md")
        with open(index_path, "r", encoding="utf-8") as f:
            lines = f.read()
        assert "Article A" in lines
        assert "Doc B" in lines
    finally:
        shutil.rmtree(base_dir)
