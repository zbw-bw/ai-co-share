# app/session_manager.py
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


class SessionManager:
    def __init__(self, base_dir: str):
        self._file = Path(base_dir) / "sessions.json"
        self._sessions: list[dict] = []
        self._load()

    def _load(self):
        if self._file.exists():
            try:
                self._sessions = json.loads(self._file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, ValueError):
                self._sessions = []

    def _save(self):
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._file.write_text(json.dumps(self._sessions, ensure_ascii=False, indent=2), encoding="utf-8")

    def save_session(self, session_id: str, first_message: str, model: str = ""):
        for s in self._sessions:
            if s["id"] == session_id:
                s["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                s["messages"] = s.get("messages", 0) + 1
                self._save()
                return
        self._sessions.insert(0, {
            "id": session_id,
            "title": first_message[:30],
            "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "model": model,
            "messages": 1,
        })
        if len(self._sessions) > 50:
            self._sessions = self._sessions[:50]
        self._save()

    def list_sessions(self, limit: int = 10) -> list[dict]:
        return self._sessions[:limit]

    def get_session(self, index: int) -> dict | None:
        if 0 <= index < len(self._sessions):
            return self._sessions[index]
        return None

    def delete_session(self, session_id: str):
        self._sessions = [s for s in self._sessions if s["id"] != session_id]
        self._save()
