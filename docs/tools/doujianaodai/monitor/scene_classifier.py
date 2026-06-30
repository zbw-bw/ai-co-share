from __future__ import annotations

import re
from dataclasses import dataclass

READING_PROCESSES = {
    "google chrome", "safari", "microsoft edge", "firefox", "brave browser",
    "arc", "preview", "adobe acrobat reader", "skim",
}

WRITING_PROCESSES = {
    "microsoft word", "pages", "wps office", "notion", "obsidian",
    "typora", "mark text", "microsoft excel", "numbers", "keynote",
    "microsoft powerpoint",
}

MIN_TEXT_LENGTH_FOR_READING = 50


@dataclass
class SceneResult:
    scene_type: str | None
    title: str
    app_name: str


def _extract_document_title(window_title: str) -> str:
    parts = re.split(r"\s[-–—|]\s", window_title)
    if parts:
        return parts[0].strip()
    return window_title.strip()


def classify_scene(
    window_title: str,
    process_name: str,
    ocr_text: str,
) -> SceneResult:
    proc = process_name.lower()
    doc_title = _extract_document_title(window_title)

    if proc in WRITING_PROCESSES:
        if len(ocr_text.strip()) > 10:
            return SceneResult(
                scene_type="writing",
                title=doc_title,
                app_name=process_name,
            )

    if proc in READING_PROCESSES:
        if len(ocr_text.strip()) >= MIN_TEXT_LENGTH_FOR_READING:
            return SceneResult(
                scene_type="reading",
                title=doc_title,
                app_name=process_name,
            )

    return SceneResult(scene_type=None, title=doc_title, app_name=process_name)
