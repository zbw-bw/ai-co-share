from __future__ import annotations

import os
import re
from pathlib import Path


class ActivityWriter:
    """Writes activity markdown files and maintains per-day index files."""

    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)
        self._counters: dict[str, int] = {}

    def _next_id(self, date: str) -> int:
        """Return the next sequential activity ID for the given date."""
        if date not in self._counters:
            activities_dir = self._base_dir / "activities" / date
            if activities_dir.exists():
                existing = list(activities_dir.glob("activity_*.md"))
                nums = []
                for f in existing:
                    m = re.search(r"activity_(\d+)\.md", f.name)
                    if m:
                        nums.append(int(m.group(1)))
                self._counters[date] = max(nums) if nums else 0
            else:
                self._counters[date] = 0
        self._counters[date] += 1
        return self._counters[date]

    def write_activity(
        self,
        date: str,
        start_time: str,
        end_time: str,
        scene_type: str,
        title: str,
        app_name: str,
        summary: str,
        content: str,
        screenshot_paths: list[str],
    ) -> str:
        """Write a new activity markdown file and update the daily index.

        Returns the absolute file path of the created activity doc.
        """
        activity_id = self._next_id(date)
        activity_dir = self._base_dir / "activities" / date
        activity_dir.mkdir(parents=True, exist_ok=True)

        filename = f"activity_{activity_id:03d}.md"
        file_path = activity_dir / filename

        scene_label = self._scene_label(scene_type)
        tags = self._generate_tags(scene_type)

        screenshots_section = ""
        if screenshot_paths:
            screenshots_section = f"截图：{', '.join(screenshot_paths)}\n"

        doc = (
            f"# {title}\n\n"
            f"时间：{date} {start_time}-{end_time}\n"
            f"场景：{scene_label}\n"
            f"来源：{app_name}\n"
            f"标签：{tags}\n"
            f"{screenshots_section}\n"
            f"## 摘要\n\n"
            f"{summary}\n\n"
            f"## 详情\n\n"
            f"{content}\n"
        )

        file_path.write_text(doc, encoding="utf-8")
        self._update_index(date, start_time, end_time, scene_type, title, file_path)
        return str(file_path)

    def update_activity(
        self,
        file_path: str,
        end_time: str,
        additional_content: str,
        screenshot_paths: list[str],
    ) -> None:
        """Update an existing activity's end time, content, and screenshots."""
        path = Path(file_path)
        text = path.read_text(encoding="utf-8")

        # Update end time: match pattern like "10:00-10:05" and replace end part
        text = re.sub(
            r"(时间：\S+\s+\S+)-\S+",
            rf"\1-{end_time}",
            text,
        )

        # Append additional content
        if additional_content:
            text = text.rstrip() + f"\n\n{additional_content}\n"

        # Add screenshots
        if screenshot_paths:
            new_shots = ", ".join(screenshot_paths)
            if "截图：" in text:
                text = re.sub(
                    r"(截图：[^\n]*)",
                    rf"\1, {new_shots}",
                    text,
                )
            else:
                # Insert screenshots line before the first blank line after metadata
                text = re.sub(
                    r"(标签：[^\n]*\n)",
                    rf"\1截图：{new_shots}\n",
                    text,
                )

        path.write_text(text, encoding="utf-8")

    def _update_index(
        self,
        date: str,
        start_time: str,
        end_time: str,
        scene_type: str,
        title: str,
        activity_path: Path,
    ) -> None:
        """Append an entry to the daily index file."""
        index_dir = self._base_dir / "index"
        index_dir.mkdir(parents=True, exist_ok=True)
        index_path = index_dir / f"{date}.md"

        rel_path = activity_path.relative_to(self._base_dir)
        scene_tag = f"#{self._scene_label(scene_type)}"
        category_tag = "#学习" if scene_type == "reading" else "#工作"
        line = f"- [{start_time}-{end_time}] {category_tag} {scene_tag} {title} → {rel_path}\n"

        if index_path.exists():
            existing = index_path.read_text(encoding="utf-8")
            index_path.write_text(existing + line, encoding="utf-8")
        else:
            header = f"# {date} 活动索引\n\n"
            index_path.write_text(header + line, encoding="utf-8")

    @staticmethod
    def _scene_label(scene_type: str) -> str:
        labels = {
            "reading": "阅读",
            "writing": "写作",
            "coding": "编码",
            "browsing": "浏览",
        }
        return labels.get(scene_type, scene_type)

    @staticmethod
    def _generate_tags(scene_type: str) -> str:
        if scene_type == "reading":
            return "学习、阅读"
        if scene_type == "writing":
            return "工作、写作"
        return scene_type
