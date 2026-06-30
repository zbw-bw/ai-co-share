from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path


def save_ocr(base_dir: str, date: str, timestamp: str, text: str) -> str:
    ocr_dir = Path(base_dir) / "ocr" / date
    ocr_dir.mkdir(parents=True, exist_ok=True)
    path = ocr_dir / f"{timestamp}.txt"
    path.write_text(text, encoding="utf-8")
    return str(path)


def load_ocr(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def cleanup_ocr_expired(base_dir: str, retention_days: int = 7) -> int:
    ocr_dir = Path(base_dir) / "ocr"
    if not ocr_dir.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for d in ocr_dir.iterdir():
        if not d.is_dir():
            continue
        try:
            dir_date = datetime.strptime(d.name, "%Y-%m-%d")
            if dir_date < cutoff:
                shutil.rmtree(d)
                removed += 1
        except ValueError:
            continue
    return removed
