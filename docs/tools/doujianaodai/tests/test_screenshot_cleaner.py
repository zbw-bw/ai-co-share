# tests/test_screenshot_cleaner.py
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from PIL import Image
from memory.screenshot_cleaner import save_screenshot, cleanup_similar, cleanup_expired


def test_save_screenshot_creates_jpeg():
    base_dir = tempfile.mkdtemp()
    try:
        img = Image.new("RGB", (800, 600), color="blue")
        path = save_screenshot(img, base_dir, "2026-06-25", "10-00-00", quality=75)
        assert os.path.exists(path)
        assert path.endswith(".jpg")
        saved = Image.open(path)
        assert saved.size == (800, 600)
    finally:
        shutil.rmtree(base_dir)


def test_cleanup_similar_removes_duplicates():
    base_dir = tempfile.mkdtemp()
    try:
        screenshot_dir = os.path.join(base_dir, "screenshots", "2026-06-25")
        os.makedirs(screenshot_dir)
        img = Image.new("RGB", (100, 100), color="red")
        img.save(os.path.join(screenshot_dir, "10-00-00.jpg"))
        img.save(os.path.join(screenshot_dir, "10-00-30.jpg"))
        img.save(os.path.join(screenshot_dir, "10-01-00.jpg"))
        different = Image.new("RGB", (100, 100), color="green")
        different.save(os.path.join(screenshot_dir, "10-01-30.jpg"))

        removed = cleanup_similar(base_dir, "2026-06-25", similarity_threshold=0.9)
        assert removed == 1  # middle identical frame removed, keep first, last, and different
        remaining = os.listdir(screenshot_dir)
        assert "10-00-00.jpg" in remaining  # first
        assert "10-01-00.jpg" not in remaining or "10-00-30.jpg" not in remaining
        assert "10-01-30.jpg" in remaining  # different color
    finally:
        shutil.rmtree(base_dir)


def test_cleanup_expired_removes_old_dirs():
    base_dir = tempfile.mkdtemp()
    try:
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        new_date = datetime.now().strftime("%Y-%m-%d")

        old_dir = os.path.join(base_dir, "screenshots", old_date)
        new_dir = os.path.join(base_dir, "screenshots", new_date)
        os.makedirs(old_dir)
        os.makedirs(new_dir)

        Image.new("RGB", (10, 10)).save(os.path.join(old_dir, "test.jpg"))
        Image.new("RGB", (10, 10)).save(os.path.join(new_dir, "test.jpg"))

        removed = cleanup_expired(base_dir, retention_days=7)
        assert removed == 1
        assert not os.path.exists(old_dir)
        assert os.path.exists(new_dir)
    finally:
        shutil.rmtree(base_dir)


from memory.screenshot_cleaner import cleanup_logs_expired


def test_cleanup_logs_expired(tmp_path):
    monitor_dir = tmp_path / "logs" / "monitor"
    monitor_dir.mkdir(parents=True)
    (monitor_dir / "2020-01-01.md").write_text("old log")
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    (monitor_dir / f"{today}.md").write_text("today log")
    removed = cleanup_logs_expired(str(tmp_path), retention_days=30)
    assert removed == 1
    assert not (monitor_dir / "2020-01-01.md").exists()
    assert (monitor_dir / f"{today}.md").exists()
