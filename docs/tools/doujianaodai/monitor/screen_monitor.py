# monitor/screen_monitor.py
from __future__ import annotations

import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from monitor.screenshot import capture_foreground_window
from monitor.idle_detector import is_user_idle
from monitor.ocr import recognize_text_with_skip, init_engine
from monitor.scene_classifier import classify_scene
from monitor.llm_client import generate_summary
from monitor.behavior_state import BehaviorStateMachine
from monitor.ocr_store import save_ocr
from memory.activity_writer import ActivityWriter
from memory.screenshot_cleaner import save_screenshot
from logs.pet_logger import MonitorLogger, StatsCollector

logger = logging.getLogger(__name__)


class ScreenMonitor:
    def __init__(
        self,
        base_dir: str,
        interval: float = 15.0,
        idle_timeout: int = 120,
        engage_threshold: int = 5,
        screenshot_quality: int = 75,
        llm_base_url: str = "http://localhost:11434",
        llm_model: str = "qwen3:8b",
        ocr_engine: str = "paddleocr",
        ocr_lang: str = "ch",
        ocr_vision_model: str = "minicpm-v",
        stats_collector: StatsCollector | None = None,
    ):
        self._base_dir = base_dir
        self._interval = interval
        self._idle_timeout = idle_timeout
        self._screenshot_quality = screenshot_quality
        self._llm_base_url = llm_base_url
        self._llm_model = llm_model

        self._writer = ActivityWriter(base_dir)
        self._state_machine = BehaviorStateMachine(engage_threshold=engage_threshold)
        self._monitor_logger = MonitorLogger(base_dir)
        self._stats = stats_collector or StatsCollector(base_dir)

        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._ocr_pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="ocr")
        self._pending_ocr = None
        self._last_ocr_result: tuple[str, str, str, str, str] | None = None

        init_engine(engine_type=ocr_engine, lang=ocr_lang,
                    vision_model=ocr_vision_model, ollama_url=llm_base_url)
        self._ocr_engine_name = ocr_vision_model if ocr_engine == "ollama_vision" else "paddleocr"

    @property
    def stats_collector(self) -> StatsCollector:
        return self._stats

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._ocr_pool.shutdown(wait=False)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            tick_start = time.time()
            try:
                self._tick()
            except Exception:
                logger.exception("Monitor tick failed")
            elapsed = time.time() - tick_start
            remaining = max(0, self._interval - elapsed)
            if remaining > 0:
                self._stop_event.wait(remaining)

    def _tick(self) -> None:
        if self._pending_ocr is not None and self._pending_ocr.done():
            self._process_ocr_result()

        if is_user_idle(self._idle_timeout):
            return

        image, title, process = capture_foreground_window()
        if image is None:
            return

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        ts_for_file = now.strftime("%H-%M-%S")
        timestamp_full = now.strftime("%Y-%m-%d %H:%M:%S")

        save_screenshot(image, self._base_dir, date_str, ts_for_file, quality=self._screenshot_quality)
        self._stats.record_screenshot()
        self._monitor_logger.log_screenshot(date_str, time_str, process, title, 0, self._ocr_engine_name)

        if self._pending_ocr is None or self._pending_ocr.done():
            self._pending_ocr = self._ocr_pool.submit(
                self._ocr_task, image, title, process, date_str, time_str, ts_for_file, timestamp_full
            )

    def _ocr_task(self, image, title, process, date_str, time_str, ts_for_file, timestamp_full):
        ocr_text, skipped = recognize_text_with_skip(image)
        if not skipped:
            save_ocr(self._base_dir, date_str, ts_for_file, ocr_text)
        scene = classify_scene(title, process, ocr_text)
        return ocr_text, scene, date_str, time_str, timestamp_full

    def _process_ocr_result(self):
        try:
            result = self._pending_ocr.result(timeout=0)
        except Exception:
            logger.exception("OCR task failed")
            self._pending_ocr = None
            return

        self._pending_ocr = None
        ocr_text, scene, date_str, time_str, timestamp_full = result

        old_state = self._state_machine.state
        action = self._state_machine.process(scene, ocr_text, timestamp_full)
        new_state = self._state_machine.state

        if old_state != new_state:
            self._monitor_logger.log_state_transition(date_str, time_str, old_state, new_state)
            self._stats.record_state_transition(old_state, new_state)

        if action.action == "generate_summary" and action.scene is not None:
            summary_thread = threading.Thread(
                target=self._generate_and_write,
                args=(action, date_str, time_str),
                daemon=True,
            )
            summary_thread.start()

    def _generate_and_write(self, action, date_str: str, time_str: str):
        start_dt = datetime.strptime(action.start_time, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.strptime(action.end_time, "%Y-%m-%d %H:%M:%S")
        duration = (end_dt - start_dt).total_seconds()

        self._stats.record_engaged_session(duration)

        llm_start = time.time()
        summary, content = generate_summary(
            action.ocr_texts,
            action.scene.title,
            action.scene.scene_type,
            duration_sec=duration,
            base_url=self._llm_base_url,
            model=self._llm_model,
        )
        llm_time = time.time() - llm_start

        self._stats.record_summary()
        self._stats.record_llm_call(llm_time)

        start_time_str = start_dt.strftime("%H:%M")
        path = self._writer.write_activity(
            date=date_str,
            start_time=start_time_str,
            end_time=time_str,
            scene_type=action.scene.scene_type,
            title=action.scene.title,
            app_name=action.scene.app_name,
            summary=summary,
            content=content,
            screenshot_paths=[],
        )

        activity_file = os.path.basename(path)
        self._monitor_logger.log_summary_generated(
            date_str, time_str, activity_file, len(action.ocr_texts), llm_time,
        )
