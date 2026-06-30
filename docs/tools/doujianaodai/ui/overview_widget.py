# ui/overview_widget.py
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt


class OverviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("📊 今日概览")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        self._content = QLabel("加载中...")
        self._content.setWordWrap(True)
        self._content.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._content.setStyleSheet("QLabel { font-size: 14px; padding: 8px; }")
        scroll.setWidget(self._content)
        layout.addWidget(scroll, stretch=1)

    def refresh(self, stats_dir: str, index_dir: str):
        today = datetime.now().strftime("%Y-%m-%d")
        lines = []

        stats_path = Path(stats_dir) / f"{today}.json"
        if stats_path.exists():
            data = json.loads(stats_path.read_text(encoding="utf-8"))
            m = data.get("monitor", {})
            c = data.get("chat", {})
            lines.append(f"截图次数    {m.get('screenshots_total', 0)}")
            lines.append(f"深度活动    {m.get('engaged_sessions', 0)} 次")
            avg_dur = m.get("engaged_avg_duration_sec", 0)
            total_min = round(m.get("engaged_sessions", 0) * avg_dur / 60, 1)
            lines.append(f"总活动时长  {total_min} 分钟")
            lines.append(f"浏览次数    {m.get('browsing_sessions', 0)} 次")
            lines.append(f"摘要生成    {m.get('summaries_generated', 0)} 次")
            lines.append(f"对话消息    {c.get('messages_total', 0)} 条")
        else:
            lines.append("暂无统计数据")

        index_path = Path(index_dir) / f"{today}.md"
        if index_path.exists():
            content = index_path.read_text(encoding="utf-8")
            activity_count = len([l for l in content.split("\n") if l.strip().startswith("- ")])
            lines.insert(1, f"识别活动    {activity_count} 条")

        self._content.setText("\n".join(lines))
