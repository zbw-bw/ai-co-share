import os
from datetime import datetime
from monitor.ocr_store import save_ocr, load_ocr, cleanup_ocr_expired


def test_save_and_load(tmp_path):
    path = save_ocr(str(tmp_path), "2026-06-26", "10-00-15", "你好世界")
    assert os.path.exists(path)
    assert path.endswith(".txt")
    assert load_ocr(path) == "你好世界"


def test_save_creates_date_dir(tmp_path):
    save_ocr(str(tmp_path), "2026-06-26", "10-00-15", "text")
    assert (tmp_path / "ocr" / "2026-06-26").is_dir()


def test_load_missing_file():
    assert load_ocr("/nonexistent/path.txt") == ""


def test_cleanup_expired(tmp_path):
    ocr_dir = tmp_path / "ocr"
    old = ocr_dir / "2020-01-01"
    old.mkdir(parents=True)
    (old / "10-00-00.txt").write_text("old")
    today = datetime.now().strftime("%Y-%m-%d")
    new = ocr_dir / today
    new.mkdir(parents=True)
    (new / "10-00-00.txt").write_text("new")
    removed = cleanup_ocr_expired(str(tmp_path), retention_days=7)
    assert removed == 1
    assert not old.exists()
    assert new.exists()
