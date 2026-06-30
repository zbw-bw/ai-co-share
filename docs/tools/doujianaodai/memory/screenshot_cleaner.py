# memory/screenshot_cleaner.py
from __future__ import annotations

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from PIL import Image


def save_screenshot(
    image: Image.Image,
    base_dir: str,
    date: str,
    timestamp: str,
    quality: int = 75,
) -> str:
    screenshot_dir = Path(base_dir) / "screenshots" / date
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{timestamp}.jpg"
    path = screenshot_dir / filename
    image.save(str(path), "JPEG", quality=quality)
    return str(path)


def _compute_ssim_channel(ch1: np.ndarray, ch2: np.ndarray) -> float:
    """Compute SSIM for a single channel (2-D array)."""
    ch1 = ch1.astype(np.float64)
    ch2 = ch2.astype(np.float64)
    mu1 = ch1.mean()
    mu2 = ch2.mean()
    sigma1_sq = ch1.var()
    sigma2_sq = ch2.var()
    sigma12 = ((ch1 - mu1) * (ch2 - mu2)).mean()
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    ssim = ((2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)
    )
    return float(ssim)


def _compute_ssim_simple(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute mean SSIM across RGB channels."""
    if img1.shape != img2.shape:
        return 0.0
    if img1.ndim == 2:
        return _compute_ssim_channel(img1, img2)
    # Average SSIM over channels
    n_channels = img1.shape[2]
    return sum(
        _compute_ssim_channel(img1[:, :, c], img2[:, :, c])
        for c in range(n_channels)
    ) / n_channels


def cleanup_similar(
    base_dir: str,
    date: str,
    similarity_threshold: float = 0.9,
) -> int:
    screenshot_dir = Path(base_dir) / "screenshots" / date
    if not screenshot_dir.exists():
        return 0

    files = sorted(screenshot_dir.glob("*.jpg"))
    if len(files) <= 2:
        return 0

    to_remove = set()
    images = []
    for f in files:
        img = Image.open(f).convert("RGB").resize((64, 64))
        images.append(np.array(img))

    for i in range(1, len(files) - 1):
        prev_sim = _compute_ssim_simple(images[i - 1], images[i])
        next_sim = _compute_ssim_simple(images[i], images[i + 1])
        if prev_sim > similarity_threshold and next_sim > similarity_threshold:
            to_remove.add(files[i])

    for f in to_remove:
        f.unlink()
    return len(to_remove)


def cleanup_expired(base_dir: str, retention_days: int = 7) -> int:
    screenshot_dir = Path(base_dir) / "screenshots"
    if not screenshot_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for d in screenshot_dir.iterdir():
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


def cleanup_logs_expired(base_dir: str, retention_days: int = 30) -> int:
    logs_dir = Path(base_dir) / "logs"
    if not logs_dir.exists():
        return 0
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for subdir in ["monitor", "chat", "stats"]:
        d = logs_dir / subdir
        if not d.exists():
            continue
        for f in d.iterdir():
            if not f.is_file():
                continue
            date_str = f.stem
            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                if file_date < cutoff:
                    f.unlink()
                    removed += 1
            except ValueError:
                continue
    return removed
