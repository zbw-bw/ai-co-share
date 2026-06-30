"""Integration test: monitor pipeline → memory write → tool retrieval.

Mocks Windows APIs and LLM, tests the full data flow.
"""
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from PIL import Image

from monitor.scene_classifier import SceneResult


def test_full_pipeline_monitor_to_retrieval():
    base_dir = tempfile.mkdtemp()
    try:
        with (
            patch("monitor.screen_monitor.capture_foreground_window") as mock_capture,
            patch("monitor.screen_monitor.is_user_idle") as mock_idle,
            patch("monitor.screen_monitor.recognize_text_with_skip") as mock_ocr,
            patch("monitor.screen_monitor.classify_scene") as mock_classify,
            patch("monitor.screen_monitor.generate_summary") as mock_summary,
        ):
            mock_idle.return_value = False
            mock_capture.return_value = (
                Image.new("RGB", (800, 600), color="white"),
                "Python异步编程指南 - Chrome",
                "Google Chrome",
            )
            mock_ocr.return_value = ("Python asyncio 是标准库中用于编写异步代码的模块。" * 5, False)

            reading_scene = SceneResult(
                scene_type="reading",
                title="Python异步编程指南",
                app_name="Google Chrome",
            )
            none_scene = SceneResult(
                scene_type=None,
                title="",
                app_name="Finder",
            )
            # Return reading scene for first 2 ticks, then None scene to
            # end the engaged session and trigger summary generation.
            mock_classify.side_effect = [reading_scene, reading_scene, none_scene, none_scene]

            mock_summary.return_value = (
                "阅读了Python异步编程指南",
                "用户在Chrome中阅读了关于Python asyncio的技术文章。",
            )

            from monitor.screen_monitor import ScreenMonitor
            from logs.pet_logger import StatsCollector
            stats = StatsCollector(base_dir)
            monitor = ScreenMonitor(
                base_dir=base_dir, interval=1, idle_timeout=120,
                engage_threshold=2, screenshot_quality=75,
                stats_collector=stats,
            )
            # With async OCR, each tick submits OCR and the NEXT tick processes results.
            import time
            for _ in range(4):
                monitor._tick()
                time.sleep(0.1)

            time.sleep(2)  # wait for background summary thread

        from app.mcp_server import handle_read_activity_index, handle_list_available_dates
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        dates = handle_list_available_dates(base_dir)
        assert today in dates
        assert dates[today] >= 1

        index_content = handle_read_activity_index(base_dir, "today")
        assert "Python异步编程指南" in index_content

        activity_dir = os.path.join(base_dir, "activities", today)
        assert os.path.exists(activity_dir)
        activity_files = os.listdir(activity_dir)
        assert len(activity_files) >= 1

    finally:
        shutil.rmtree(base_dir)
