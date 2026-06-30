# ui/activity_log_widget.py
from __future__ import annotations

import re
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QTextEdit, QDateEdit,
)
from PyQt6.QtCore import Qt, QDate


class ActivityLogWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_dir = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header = QHBoxLayout()
        header.addWidget(QLabel("📋 活动日志"))
        header.addStretch()
        self._date_edit = QDateEdit()
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setCalendarPopup(True)
        self._date_edit.dateChanged.connect(self._on_date_changed)
        header.addWidget(self._date_edit)
        layout.addLayout(header)

        self._list = QListWidget()
        self._list.setStyleSheet("QListWidget { font-size: 13px; }")
        self._list.currentItemChanged.connect(self._on_item_selected)
        layout.addWidget(self._list, stretch=1)

        self._detail = QTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setMaximumHeight(150)
        self._detail.setStyleSheet(
            "QTextEdit { background-color: #fafafa; border: 1px solid #eee; "
            "border-radius: 6px; padding: 6px; font-size: 13px; }"
        )
        layout.addWidget(self._detail)

        self._count_label = QLabel("共 0 条记录")
        self._count_label.setStyleSheet("QLabel { color: #888; font-size: 12px; }")
        layout.addWidget(self._count_label)

    def set_base_dir(self, base_dir: str):
        self._base_dir = base_dir
        self._on_date_changed(self._date_edit.date())

    def _on_date_changed(self, date: QDate):
        date_str = date.toString("yyyy-MM-dd")
        self._list.clear()
        self._detail.clear()
        total = 0

        total += self._load_activities(date_str)
        total += self._load_chat_logs(date_str)

        self._count_label.setText(f"共 {total} 条记录" if total > 0 else "该日期无记录")

    def _load_activities(self, date: str) -> int:
        index_path = Path(self._base_dir) / "index" / f"{date}.md"
        if not index_path.exists():
            return 0

        content = index_path.read_text(encoding="utf-8")
        entries = [l.strip() for l in content.split("\n") if l.strip().startswith("- ")]

        for entry in entries:
            item = QListWidgetItem(f"📝 {entry[2:]}")
            match = re.search(r"→\s*(.+)$", entry)
            if match:
                item.setData(Qt.ItemDataRole.UserRole, str(Path(self._base_dir) / match.group(1).strip()))
            self._list.addItem(item)

        return len(entries)

    def _load_chat_logs(self, date: str) -> int:
        chat_path = Path(self._base_dir) / "logs" / "chat" / f"{date}.md"
        if not chat_path.exists():
            return 0

        content = chat_path.read_text(encoding="utf-8")
        conversations = re.split(r"\n---\n", content)
        count = 0

        for conv in conversations:
            conv = conv.strip()
            if not conv:
                continue
            time_match = re.search(r"## (\d{2}:\d{2}:\d{2})", conv)
            user_match = re.search(r"\*\*用户\*\*:\s*(.+)", conv)
            if time_match and user_match:
                time_str = time_match.group(1)
                user_msg = user_match.group(1).strip()[:40]
                item = QListWidgetItem(f"💬 [{time_str}] {user_msg}")
                item.setData(Qt.ItemDataRole.UserRole, f"__chat__:{conv}")
                self._list.addItem(item)
                count += 1

        return count

    def load_date(self, index_dir: str, activities_dir: str, date: str):
        self._on_date_changed(QDate.fromString(date, "yyyy-MM-dd"))

    def _on_item_selected(self, current: QListWidgetItem | None, _previous):
        if current is None:
            self._detail.clear()
            return
        data = current.data(Qt.ItemDataRole.UserRole)
        if not data:
            self._detail.clear()
            return

        if isinstance(data, str) and data.startswith("__chat__:"):
            chat_content = data[9:]
            self._detail.setPlainText(chat_content.strip())
        elif Path(data).exists():
            text = Path(data).read_text(encoding="utf-8")
            ocr_stripped = re.sub(r"\n*### OCR原文片段\n+```\n.*?```\n?", "", text, flags=re.DOTALL)
            self._detail.setPlainText(ocr_stripped.strip())
        else:
            self._detail.setPlainText("无法加载详情")
