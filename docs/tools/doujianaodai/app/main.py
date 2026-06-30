# app/main.py
"""Application entry point — orchestrates monitor, Claude Code bridge, and UI."""
from __future__ import annotations

import logging
import sys
import os
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

from app.config import load_config
from app.claude_client import ClaudeClient
from app.session_manager import SessionManager
from monitor.screen_monitor import ScreenMonitor
from memory.summary_generator import SummaryGenerator
from logs.pet_logger import ChatLogger, StatsCollector
from ui.tray_app import TrayApp

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

MEMORY_DIR = os.path.expanduser("~/.pet-memory")


class ChatWorker(QThread):
    stream_event = pyqtSignal(dict)
    finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, client: ClaudeClient, message: str):
        super().__init__()
        self._client = client
        self._message = message

    def run(self):
        try:
            for event in self._client.send_message_stream(self._message):
                self.stream_event.emit(event.to_dict())
        except Exception as e:
            self.error_occurred.emit(f"对话出错: {e}")
        self.finished.emit()


class PetApp:
    def __init__(self, config: dict | None = None, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
        self._config_path = config_path

        if config is not None:
            self._config = config
        else:
            self._config = load_config(config_path)

        os.makedirs(MEMORY_DIR, exist_ok=True)

        self._stats = StatsCollector(MEMORY_DIR)
        self._chat_logger = ChatLogger(MEMORY_DIR)

        self._client = ClaudeClient(
            chat_logger=self._chat_logger,
            stats_collector=self._stats,
        )
        self._monitor = ScreenMonitor(
            base_dir=MEMORY_DIR,
            interval=self._config["monitor"]["interval_seconds"],
            idle_timeout=self._config["monitor"]["idle_timeout_seconds"],
            engage_threshold=self._config["monitor"].get("engage_threshold", 5),
            screenshot_quality=self._config["screenshots"]["quality"],
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
            ocr_engine=self._config["ocr"].get("engine", "paddleocr"),
            ocr_lang=self._config["ocr"].get("lang", "ch"),
            ocr_vision_model=self._config["ocr"].get("vision_model", "minicpm-v"),
            stats_collector=self._stats,
        )
        self._summary_gen = SummaryGenerator(
            base_dir=MEMORY_DIR,
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._tray: TrayApp | None = None
        self._health_timer: QTimer | None = None
        self._chat_worker: ChatWorker | None = None
        self._session_mgr = SessionManager(MEMORY_DIR)
        self._current_first_msg: str | None = None

    def run(self):
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        self._tray = TrayApp(
            config=self._config,
            config_path=self._config_path,
            on_message_sent=self._on_user_message,
        )

        self._start_services()

        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(30000)

        exit_code = app.exec()
        self._shutdown()
        sys.exit(exit_code)

    def _start_services(self):
        if self._tray:
            self._tray.chat_widget.append_message("system", "逗叽脑袋已启动，对话将通过 Claude Code 处理。")
            self._tray.update_agent_status(True)

        if self._config["monitor"]["enabled"]:
            self._monitor.start()
            if self._tray:
                self._tray.update_monitor_status(True)

        self._summary_gen.check_and_generate_pending()

        if self._tray:
            self._tray.activity_log_widget.set_base_dir(MEMORY_DIR)
            self._tray.overview_widget.refresh(
                stats_dir=str(os.path.join(MEMORY_DIR, "logs", "stats")),
                index_dir=str(os.path.join(MEMORY_DIR, "index")),
            )

    def _on_user_message(self, text: str):
        if text.startswith("/"):
            self._handle_command(text)
            return

        if self._current_first_msg is None:
            self._current_first_msg = text

        if self._tray:
            self._tray.chat_widget.set_input_enabled(False)

        self._chat_worker = ChatWorker(self._client, text)
        self._chat_worker.stream_event.connect(self._on_stream_event)
        self._chat_worker.error_occurred.connect(self._on_error)
        self._chat_worker.finished.connect(self._on_chat_finished)
        self._chat_worker.start()

    def _handle_command(self, text: str):
        parts = text.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/clear":
            self._client.clear_conversation()
            self._current_first_msg = None
            if self._tray:
                self._tray.chat_widget.clear_chat()
                self._tray.chat_widget.append_message("system", "对话已清空。")

        elif cmd == "/project":
            if not arg:
                current = self._client._project_dir or "未设置（使用默认目录）"
                if self._tray:
                    self._tray.chat_widget.append_message("system", f"当前项目目录: {current}\n用法: /project /path/to/dir")
            else:
                expanded = os.path.expanduser(arg)
                if os.path.isdir(expanded):
                    self._client._project_dir = expanded
                    if self._tray:
                        self._tray.chat_widget.append_message("system", f"项目目录已设置: {expanded}")
                else:
                    if self._tray:
                        self._tray.chat_widget.append_message("system", f"目录不存在: {expanded}")

        elif cmd == "/model":
            if arg:
                self._client._model_override = arg
                if self._tray:
                    self._tray.chat_widget.append_message("system", f"Claude 对话模型已切换: {arg}\n下次对话生效。输入 /model 不带参数可恢复默认。")
            else:
                current_llm = self._config["llm"]["local"]["model"]
                current_claude = getattr(self._client, '_model_override', None) or "默认（由 Claude Code 决定）"
                if self._tray:
                    self._tray.chat_widget.append_message(
                        "system",
                        f"摘要模型: {current_llm}\n"
                        f"对话模型: {current_claude}\n"
                        f"用法: /model claude-sonnet-4-20250514"
                    )

        elif cmd == "/status":
            monitor_ok = self._monitor.is_running()
            session = self._client._session_id or "无"
            project = self._client._project_dir or "默认"
            model = getattr(self._client, '_model_override', None) or "默认"
            if self._tray:
                self._tray.chat_widget.append_message(
                    "system",
                    f"监控: {'运行中' if monitor_ok else '已停止'}\n"
                    f"会话: {session}\n"
                    f"项目目录: {project}\n"
                    f"对话模型: {model}"
                )

        elif cmd == "/cost":
            cost = self._client._last_cost
            if cost:
                usd = cost.get("total_cost_usd", 0)
                inp = cost.get("input_tokens", 0)
                out = cost.get("output_tokens", 0)
                dur = cost.get("duration_ms", 0) / 1000
                if self._tray:
                    self._tray.chat_widget.append_message(
                        "system",
                        f"上次对话消耗:\n"
                        f"输入 tokens: {inp:,}\n"
                        f"输出 tokens: {out:,}\n"
                        f"费用: ${usd:.4f}\n"
                        f"耗时: {dur:.1f}s"
                    )
            else:
                if self._tray:
                    self._tray.chat_widget.append_message("system", "暂无对话记录。先发一条消息再查看费用。")

        elif cmd == "/bug":
            import webbrowser
            webbrowser.open("https://github.com/anthropics/claude-code/issues")
            if self._tray:
                self._tray.chat_widget.append_message("system", "已打开 Claude Code Issues 页面。")

        elif cmd == "/list":
            sessions = self._session_mgr.list_sessions()
            if not sessions:
                if self._tray:
                    self._tray.chat_widget.append_message("system", "没有历史会话。")
            else:
                lines = ["历史会话（输入 /resume 序号 继续）:\n"]
                for i, s in enumerate(sessions):
                    active = " ← 当前" if s["id"] == self._client._session_id else ""
                    lines.append(f"{i+1}. [{s['updated']}] {s['title']} ({s['messages']}条){active}")
                if self._tray:
                    self._tray.chat_widget.append_message("system", "\n".join(lines))

        elif cmd == "/resume":
            if not arg:
                if self._tray:
                    self._tray.chat_widget.append_message("system", "用法: /resume 序号\n先用 /list 查看可用会话。")
            else:
                try:
                    idx = int(arg) - 1
                    s = self._session_mgr.get_session(idx)
                    if s:
                        self._client._session_id = s["id"]
                        self._current_first_msg = s["title"]
                        if self._tray:
                            self._tray.chat_widget.clear_chat()
                            self._tray.chat_widget.append_message(
                                "system", f"已切换到会话: {s['title']}\n创建于 {s['created']}，共 {s['messages']} 条消息。"
                            )
                    else:
                        if self._tray:
                            self._tray.chat_widget.append_message("system", f"无效序号: {arg}")
                except ValueError:
                    if self._tray:
                        self._tray.chat_widget.append_message("system", f"请输入数字序号，如: /resume 1")

        elif cmd == "/session":
            session = self._client._session_id or "无"
            if self._tray:
                self._tray.chat_widget.append_message("system", f"当前会话: {session}\n用 /clear 可重置会话。")

        elif cmd == "/regenerate":
            self._regenerate_summaries(arg)

        elif cmd == "/doctor":
            self._run_claude_subcommand(["claude", "doctor"])

        elif cmd == "/config":
            self._run_claude_subcommand(["claude", "config", "list"])

        elif cmd == "/help":
            if self._tray:
                self._tray.chat_widget.append_message(
                    "system",
                    "可用命令:\n"
                    "/clear — 清空对话，开始新会话\n"
                    "/list — 查看历史会话列表\n"
                    "/resume <序号> — 继续历史会话\n"
                    "/project <路径> — 设置 Claude Code 工作目录\n"
                    "/model [名称] — 查看/切换 Claude 对话模型\n"
                    "/cost — 查看上次对话的 token 消耗和费用\n"
                    "/session — 查看当前会话 ID\n"
                    "/regenerate [日期] — 重新生成摘要（默认今天）\n"
                    "/status — 查看运行状态\n"
                    "/doctor — Claude Code 健康检查\n"
                    "/config — 查看 Claude Code 配置\n"
                    "/bug — 打开 Claude Code Issues 页面\n"
                    "/help — 显示此帮助"
                )
        else:
            if self._tray:
                self._tray.chat_widget.append_message("system", f"未知命令: {cmd}\n输入 /help 查看可用命令。")

    def _run_claude_subcommand(self, cmd: list[str]):
        import subprocess
        if self._tray:
            self._tray.chat_widget.append_message("system", f"执行: {' '.join(cmd)}...")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout.strip() or result.stderr.strip() or "(无输出)"
            if self._tray:
                self._tray.chat_widget.append_message("system", output[:1000])
        except FileNotFoundError:
            if self._tray:
                self._tray.chat_widget.append_message("system", "Claude Code CLI 未找到。")
        except subprocess.TimeoutExpired:
            if self._tray:
                self._tray.chat_widget.append_message("system", "命令超时。")
        except Exception as e:
            if self._tray:
                self._tray.chat_widget.append_message("system", f"执行失败: {e}")

    def _regenerate_summaries(self, date_arg: str):
        import re
        from pathlib import Path
        from monitor.llm_client import generate_summary

        date = date_arg.strip() if date_arg else datetime.now().strftime("%Y-%m-%d")
        activities_dir = Path(MEMORY_DIR) / "activities" / date

        if not activities_dir.exists():
            if self._tray:
                self._tray.chat_widget.append_message("system", f"没有 {date} 的活动记录。")
            return

        files = sorted(activities_dir.glob("activity_*.md"))
        if not files:
            if self._tray:
                self._tray.chat_widget.append_message("system", f"{date} 没有活动文件。")
            return

        if self._tray:
            self._tray.chat_widget.append_message("system", f"正在重新生成 {date} 的 {len(files)} 条摘要...")

        regenerated = 0
        for f in files:
            content = f.read_text(encoding="utf-8")
            ocr_match = re.search(r"### OCR原文片段\n+```\n(.*?)```", content, flags=re.DOTALL)
            if not ocr_match:
                continue

            ocr_text = ocr_match.group(1).strip()
            title_match = re.match(r"# (.+)", content)
            title = title_match.group(1) if title_match else "unknown"
            scene_match = re.search(r"场景：(.+)", content)
            scene_type = "reading" if scene_match and "阅读" in scene_match.group(1) else "writing"

            try:
                summary, detail = generate_summary(
                    [ocr_text], title, scene_type,
                    base_url=self._config["llm"]["local"]["base_url"],
                    model=self._config["llm"]["local"]["model"],
                )
                new_content = re.sub(r"## 摘要\n\n.+?\n\n## 详情\n\n.+?(\n\n### OCR|$)",
                                     f"## 摘要\n\n{summary}\n\n## 详情\n\n{detail}\n\n### OCR",
                                     content, count=1, flags=re.DOTALL)
                if new_content != content:
                    f.write_text(new_content, encoding="utf-8")
                    regenerated += 1
            except Exception as e:
                logger.error("Regenerate failed for %s: %s", f.name, e)

        if self._tray:
            self._tray.chat_widget.append_message("system", f"完成！重新生成了 {regenerated}/{len(files)} 条摘要。")

    def _on_stream_event(self, event: dict):
        if self._tray:
            self._tray.chat_widget.handle_stream_event(event)

    def _on_chat_finished(self):
        if self._client._session_id and self._current_first_msg:
            model = getattr(self._client, '_model_override', None) or ""
            self._session_mgr.save_session(self._client._session_id, self._current_first_msg, model)

        if self._tray:
            self._tray.chat_widget.set_input_enabled(True)
            self._tray.overview_widget.refresh(
                stats_dir=str(os.path.join(MEMORY_DIR, "logs", "stats")),
                index_dir=str(os.path.join(MEMORY_DIR, "index")),
            )

    def _on_error(self, error: str):
        if self._tray:
            self._tray.chat_widget.append_message("system", error)
            self._tray.chat_widget.set_input_enabled(True)

    def _check_health(self):
        monitor_ok = self._monitor.is_running()
        if self._tray:
            self._tray.update_monitor_status(monitor_ok)

    def _shutdown(self):
        logger.info("Shutting down...")
        self._monitor.stop()

        today = datetime.now().strftime("%Y-%m-%d")

        self._stats.flush(today)
        self._summary_gen.generate_daily(today)

        from memory.screenshot_cleaner import cleanup_similar, cleanup_expired, cleanup_logs_expired
        from monitor.ocr_store import cleanup_ocr_expired

        cleanup_similar(MEMORY_DIR, today, self._config["screenshots"]["cleanup_similarity"])
        cleanup_expired(MEMORY_DIR, self._config["screenshots"]["retention_days"])
        cleanup_ocr_expired(MEMORY_DIR, self._config["ocr"].get("retention_days", 7))
        cleanup_logs_expired(MEMORY_DIR, self._config.get("logs", {}).get("retention_days", 30))

        logger.info("Shutdown complete")


def main():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    try:
        from app.preflight import run_preflight
        config = run_preflight(config_path)
    except SystemExit:
        return
    pet = PetApp(config=config, config_path=config_path)
    pet.run()


if __name__ == "__main__":
    main()
