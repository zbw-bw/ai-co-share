# 截图规则引擎与日志系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the naive two-shot screenshot merger with a four-state behavior state machine, add OCR persistence, and build a three-tier logging system for traceability and effectiveness evaluation.

**Architecture:** A `BehaviorStateMachine` replaces `ActivityMerger`, consuming scene + OCR text each tick and emitting actions (collect / generate_summary / skip). OCR results persist to `~/.pet-memory/ocr/` as `.txt` files mirroring screenshot timestamps. A `PetLogger` writes monitor events, chat exchanges, and daily stats to `~/.pet-memory/logs/`.

**Tech Stack:** Python 3.11, PaddleOCR, Ollama (qwen3:8b), PyQt6, macOS Quartz

## Global Constraints

- All memory stored as files under `~/.pet-memory/` — no databases
- Screenshot interval: 15 seconds
- Minimum ENGAGED threshold: 5 consecutive observations (≥75s)
- OCR text similarity: bigram Jaccard, thresholds 0.7/0.3
- Python 3.11+, macOS first
- Tests use pytest, run with `python3.11 -m pytest tests/ -v`

---

### Task 1: Text Similarity Module

**Files:**
- Create: `monitor/text_similarity.py`
- Test: `tests/test_text_similarity.py`

**Interfaces:**
- Consumes: nothing
- Produces: `text_similarity(text_a: str, text_b: str) -> float` — used by Task 3 (BehaviorStateMachine)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_text_similarity.py
from monitor.text_similarity import text_similarity


def test_identical_texts():
    assert text_similarity("你好世界", "你好世界") == 1.0


def test_empty_texts():
    assert text_similarity("", "hello") == 0.0
    assert text_similarity("hello", "") == 0.0
    assert text_similarity("", "") == 0.0


def test_completely_different():
    score = text_similarity("ABCDEF", "xyz123")
    assert score < 0.1


def test_similar_texts():
    a = "Kubernetes Pod 调度策略包括预选和优选两个阶段"
    b = "Kubernetes Pod 调度策略包括预选和优选两个阶段，其中预选负责过滤"
    score = text_similarity(a, b)
    assert 0.5 < score < 1.0


def test_gradual_change():
    base = "用户正在阅读关于机器学习的文档内容"
    scrolled = "关于机器学习的文档内容包括监督学习和非监督学习"
    score = text_similarity(base, scrolled)
    assert 0.3 <= score <= 0.7


def test_single_char():
    assert text_similarity("a", "a") == 0.0
    assert text_similarity("ab", "ab") == 1.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_text_similarity.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# monitor/text_similarity.py
from __future__ import annotations


def text_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0
    if len(text_a) < 2 or len(text_b) < 2:
        return 0.0
    bigrams_a = set(zip(text_a, text_a[1:]))
    bigrams_b = set(zip(text_b, text_b[1:]))
    intersection = bigrams_a & bigrams_b
    union = bigrams_a | bigrams_b
    return len(intersection) / len(union) if union else 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3.11 -m pytest tests/test_text_similarity.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/text_similarity.py tests/test_text_similarity.py
git commit -m "feat: add bigram Jaccard text similarity module"
```

---

### Task 2: OCR Store Module

**Files:**
- Create: `monitor/ocr_store.py`
- Test: `tests/test_ocr_store.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `save_ocr(base_dir: str, date: str, timestamp: str, text: str) -> str` — returns file path. Used by Task 5 (screen_monitor).
  - `load_ocr(path: str) -> str` — returns OCR text. Used by Task 5.
  - `cleanup_ocr_expired(base_dir: str, retention_days: int) -> int` — returns count of removed dirs. Used by Task 7 (main.py).

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ocr_store.py
import os
import tempfile
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
    # Create old dir
    old = ocr_dir / "2020-01-01"
    old.mkdir(parents=True)
    (old / "10-00-00.txt").write_text("old")
    # Create recent dir
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    new = ocr_dir / today
    new.mkdir(parents=True)
    (new / "10-00-00.txt").write_text("new")

    removed = cleanup_ocr_expired(str(tmp_path), retention_days=7)
    assert removed == 1
    assert not old.exists()
    assert new.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_ocr_store.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# monitor/ocr_store.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3.11 -m pytest tests/test_ocr_store.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/ocr_store.py tests/test_ocr_store.py
git commit -m "feat: add OCR result persistence store"
```

---

### Task 3: Behavior State Machine

**Files:**
- Create: `monitor/behavior_state.py`
- Test: `tests/test_behavior_state.py`
- Delete: `memory/activity_merger.py` (replaced)
- Delete: `tests/test_activity_merger.py` (replaced)

**Interfaces:**
- Consumes: `text_similarity` from Task 1, `SceneResult` from `monitor/scene_classifier.py`
- Produces:
  - `BehaviorStateMachine` class with method `process(scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction`
  - `StateAction` dataclass with fields: `action: str` ("skip"|"collect"|"generate_summary"), `ocr_texts: list[str]`, `scene: SceneResult | None`, `start_time: str | None`, `end_time: str | None`
  - Used by Task 5 (screen_monitor)

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_behavior_state.py
from monitor.behavior_state import BehaviorStateMachine, StateAction
from monitor.scene_classifier import SceneResult


def _scene(scene_type="reading", title="K8s Docs", app="Google Chrome"):
    return SceneResult(scene_type=scene_type, title=title, app_name=app)


def _none_scene():
    return SceneResult(scene_type=None, title="Desktop", app_name="Finder")


OCR_A = "Kubernetes Pod 调度策略包括预选Predicate和优选Priority两个阶段"
OCR_A2 = "Kubernetes Pod 调度策略包括预选Predicate和优选Priority两个阶段，其中预选负责过滤不满足条件的节点"
OCR_B = "Python asyncio 是一个用于编写并发代码的库，使用async和await语法"


class TestIdleToObserving:
    def test_first_scene_returns_collect(self):
        sm = BehaviorStateMachine(engage_threshold=5)
        action = sm.process(_scene(), OCR_A, "2026-06-26 10:00:00")
        assert action.action == "collect"

    def test_none_scene_returns_skip(self):
        sm = BehaviorStateMachine(engage_threshold=5)
        action = sm.process(_none_scene(), "", "2026-06-26 10:00:00")
        assert action.action == "skip"


class TestObservingToEngaged:
    def test_five_similar_promotes_to_engaged(self):
        sm = BehaviorStateMachine(engage_threshold=5)
        for i in range(4):
            action = sm.process(_scene(), OCR_A, f"2026-06-26 10:00:{i*15:02d}")
            assert action.action == "collect"
        action = sm.process(_scene(), OCR_A, "2026-06-26 10:01:00")
        assert action.action == "collect"
        assert sm.state == "ENGAGED"

    def test_content_mutation_resets_observing(self):
        sm = BehaviorStateMachine(engage_threshold=5)
        sm.process(_scene(), OCR_A, "2026-06-26 10:00:00")
        sm.process(_scene(), OCR_A, "2026-06-26 10:00:15")
        action = sm.process(_scene(), OCR_B, "2026-06-26 10:00:30")
        assert action.action == "collect"
        assert sm._obs_count == 1

    def test_two_consecutive_mutations_go_to_browsing(self):
        sm = BehaviorStateMachine(engage_threshold=5)
        sm.process(_scene(), OCR_A, "2026-06-26 10:00:00")
        sm.process(_scene(), OCR_B, "2026-06-26 10:00:15")
        sm.process(_scene(), "完全不同的第三段内容关于数据库设计", "2026-06-26 10:00:30")
        assert sm.state == "BROWSING"


class TestEngagedExit:
    def _enter_engaged(self):
        sm = BehaviorStateMachine(engage_threshold=3)
        for i in range(3):
            sm.process(_scene(), OCR_A, f"2026-06-26 10:00:{i*15:02d}")
        assert sm.state == "ENGAGED"
        return sm

    def test_content_mutation_triggers_summary(self):
        sm = self._enter_engaged()
        action = sm.process(_scene(), OCR_B, "2026-06-26 10:01:00")
        assert action.action == "generate_summary"
        assert len(action.ocr_texts) >= 3
        assert action.start_time is not None

    def test_window_switch_triggers_summary(self):
        sm = self._enter_engaged()
        new_scene = _scene(title="Different Page", app="Safari")
        action = sm.process(new_scene, OCR_B, "2026-06-26 10:01:00")
        assert action.action == "generate_summary"

    def test_none_scene_triggers_summary(self):
        sm = self._enter_engaged()
        action = sm.process(_none_scene(), "", "2026-06-26 10:01:00")
        assert action.action == "generate_summary"

    def test_gradual_change_stays_engaged(self):
        sm = self._enter_engaged()
        action = sm.process(_scene(), OCR_A2, "2026-06-26 10:01:00")
        assert action.action == "collect"
        assert sm.state == "ENGAGED"


class TestBrowsing:
    def test_stable_content_exits_browsing(self):
        sm = BehaviorStateMachine(engage_threshold=3)
        sm.process(_scene(), OCR_A, "2026-06-26 10:00:00")
        sm.process(_scene(), OCR_B, "2026-06-26 10:00:15")
        sm.process(_scene(), "第三段不同内容", "2026-06-26 10:00:30")
        assert sm.state == "BROWSING"
        for i in range(3):
            sm.process(_scene(), OCR_A, f"2026-06-26 10:01:{i*15:02d}")
        assert sm.state == "ENGAGED"

    def test_none_scene_exits_browsing_to_idle(self):
        sm = BehaviorStateMachine(engage_threshold=3)
        sm.process(_scene(), OCR_A, "2026-06-26 10:00:00")
        sm.process(_scene(), OCR_B, "2026-06-26 10:00:15")
        sm.process(_scene(), "第三段不同内容", "2026-06-26 10:00:30")
        assert sm.state == "BROWSING"
        action = sm.process(_none_scene(), "", "2026-06-26 10:00:45")
        assert action.action == "skip"
        assert sm.state == "IDLE"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_behavior_state.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# monitor/behavior_state.py
from __future__ import annotations

from dataclasses import dataclass, field
from monitor.scene_classifier import SceneResult
from monitor.text_similarity import text_similarity


@dataclass
class StateAction:
    action: str  # "skip" | "collect" | "generate_summary"
    ocr_texts: list[str] = field(default_factory=list)
    scene: SceneResult | None = None
    start_time: str | None = None
    end_time: str | None = None


class BehaviorStateMachine:
    SIMILAR_THRESHOLD = 0.7
    MUTATION_THRESHOLD = 0.3

    def __init__(self, engage_threshold: int = 5):
        self._engage_threshold = engage_threshold
        self.state: str = "IDLE"

        # OBSERVING state
        self._obs_count: int = 0
        self._obs_scene: SceneResult | None = None
        self._obs_last_ocr: str = ""
        self._obs_ocr_texts: list[str] = []
        self._obs_start_time: str | None = None
        self._consecutive_mutations: int = 0

        # ENGAGED state
        self._eng_scene: SceneResult | None = None
        self._eng_last_ocr: str = ""
        self._eng_ocr_texts: list[str] = []
        self._eng_start_time: str | None = None

        # BROWSING state
        self._browse_count: int = 0
        self._browse_last_ocr: str = ""

    def process(self, scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction:
        if scene.scene_type is None:
            return self._handle_none_scene(timestamp)

        if self.state == "IDLE":
            return self._handle_idle(scene, ocr_text, timestamp)
        elif self.state == "OBSERVING":
            return self._handle_observing(scene, ocr_text, timestamp)
        elif self.state == "ENGAGED":
            return self._handle_engaged(scene, ocr_text, timestamp)
        elif self.state == "BROWSING":
            return self._handle_browsing(scene, ocr_text, timestamp)
        return StateAction(action="skip")

    def _handle_none_scene(self, timestamp: str) -> StateAction:
        if self.state == "ENGAGED":
            action = self._emit_summary(timestamp)
            self._reset_to_idle()
            return action
        self._reset_to_idle()
        return StateAction(action="skip")

    def _handle_idle(self, scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction:
        self.state = "OBSERVING"
        self._obs_count = 1
        self._obs_scene = scene
        self._obs_last_ocr = ocr_text
        self._obs_ocr_texts = [ocr_text]
        self._obs_start_time = timestamp
        self._consecutive_mutations = 0
        return StateAction(action="collect")

    def _handle_observing(self, scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction:
        sim = text_similarity(self._obs_last_ocr, ocr_text)

        if sim >= self.MUTATION_THRESHOLD:
            self._consecutive_mutations = 0
            self._obs_count += 1
            self._obs_last_ocr = ocr_text
            self._obs_ocr_texts.append(ocr_text)

            if self._obs_count >= self._engage_threshold:
                self.state = "ENGAGED"
                self._eng_scene = self._obs_scene
                self._eng_last_ocr = ocr_text
                self._eng_ocr_texts = list(self._obs_ocr_texts)
                self._eng_start_time = self._obs_start_time
                self._clear_observing()
            return StateAction(action="collect")
        else:
            self._consecutive_mutations += 1
            if self._consecutive_mutations >= 2:
                self.state = "BROWSING"
                self._browse_count = 1
                self._browse_last_ocr = ocr_text
                self._clear_observing()
                return StateAction(action="collect")
            self._obs_count = 1
            self._obs_scene = scene
            self._obs_last_ocr = ocr_text
            self._obs_ocr_texts = [ocr_text]
            self._obs_start_time = timestamp
            return StateAction(action="collect")

    def _handle_engaged(self, scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction:
        same_window = (
            scene.app_name == self._eng_scene.app_name
            and scene.title == self._eng_scene.title
        )
        sim = text_similarity(self._eng_last_ocr, ocr_text)

        if same_window and sim >= self.MUTATION_THRESHOLD:
            self._eng_last_ocr = ocr_text
            self._eng_ocr_texts.append(ocr_text)
            return StateAction(action="collect")

        action = self._emit_summary(timestamp)
        if scene.scene_type is not None:
            self.state = "OBSERVING"
            self._obs_count = 1
            self._obs_scene = scene
            self._obs_last_ocr = ocr_text
            self._obs_ocr_texts = [ocr_text]
            self._obs_start_time = timestamp
            self._consecutive_mutations = 0
        else:
            self._reset_to_idle()
        return action

    def _handle_browsing(self, scene: SceneResult, ocr_text: str, timestamp: str) -> StateAction:
        sim = text_similarity(self._browse_last_ocr, ocr_text)

        if sim >= self.MUTATION_THRESHOLD:
            self._browse_count += 1
            self._browse_last_ocr = ocr_text
            if self._browse_count >= self._engage_threshold:
                self.state = "OBSERVING"
                self._obs_count = self._browse_count
                self._obs_scene = scene
                self._obs_last_ocr = ocr_text
                self._obs_ocr_texts = [ocr_text]
                self._obs_start_time = timestamp
                self._consecutive_mutations = 0
                if self._obs_count >= self._engage_threshold:
                    self.state = "ENGAGED"
                    self._eng_scene = scene
                    self._eng_last_ocr = ocr_text
                    self._eng_ocr_texts = list(self._obs_ocr_texts)
                    self._eng_start_time = self._obs_start_time
                    self._clear_observing()
        else:
            self._browse_count = 1
            self._browse_last_ocr = ocr_text
        return StateAction(action="collect")

    def _emit_summary(self, end_time: str) -> StateAction:
        return StateAction(
            action="generate_summary",
            ocr_texts=list(self._eng_ocr_texts),
            scene=self._eng_scene,
            start_time=self._eng_start_time,
            end_time=end_time,
        )

    def _reset_to_idle(self):
        self.state = "IDLE"
        self._clear_observing()
        self._eng_scene = None
        self._eng_last_ocr = ""
        self._eng_ocr_texts = []
        self._eng_start_time = None
        self._browse_count = 0
        self._browse_last_ocr = ""

    def _clear_observing(self):
        self._obs_count = 0
        self._obs_scene = None
        self._obs_last_ocr = ""
        self._obs_ocr_texts = []
        self._obs_start_time = None
        self._consecutive_mutations = 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3.11 -m pytest tests/test_behavior_state.py -v`
Expected: all PASS

- [ ] **Step 5: Delete old merger and its tests**

```bash
rm memory/activity_merger.py tests/test_activity_merger.py
```

- [ ] **Step 6: Commit**

```bash
git add monitor/behavior_state.py tests/test_behavior_state.py
git add -u memory/activity_merger.py tests/test_activity_merger.py
git commit -m "feat: replace ActivityMerger with BehaviorStateMachine"
```

---

### Task 4: Pet Logger Module

**Files:**
- Create: `logs/pet_logger.py`
- Create: `logs/__init__.py`
- Test: `tests/test_pet_logger.py`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `MonitorLogger` class: `log_screenshot(...)`, `log_state_transition(...)`, `log_summary_generated(...)` — used by Task 5
  - `ChatLogger` class: `log_conversation(...)` — used by Task 6
  - `StatsCollector` class: `record_screenshot()`, `record_state_transition(from_state, to_state)`, `record_engaged_session(duration)`, `record_summary()`, `record_llm_call(duration)`, `record_chat(response_time, tools)`, `flush(date)` — used by Tasks 5, 6, 7

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pet_logger.py
import json
from logs.pet_logger import MonitorLogger, ChatLogger, StatsCollector


class TestMonitorLogger:
    def test_log_screenshot(self, tmp_path):
        ml = MonitorLogger(str(tmp_path))
        ml.log_screenshot("2026-06-26", "10:00:15", "Google Chrome", "K8s Docs", 856)
        log_file = tmp_path / "logs" / "monitor" / "2026-06-26.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert "SCREENSHOT" in content
        assert "Google Chrome" in content
        assert "856" in content

    def test_log_state_transition(self, tmp_path):
        ml = MonitorLogger(str(tmp_path))
        ml.log_state_transition("2026-06-26", "10:00:16", "IDLE", "OBSERVING", "检测到reading场景")
        log_file = tmp_path / "logs" / "monitor" / "2026-06-26.md"
        content = log_file.read_text()
        assert "IDLE → OBSERVING" in content

    def test_log_summary_generated(self, tmp_path):
        ml = MonitorLogger(str(tmp_path))
        ml.log_summary_generated("2026-06-26", "10:05:31", "activity_003.md", 18, 3.2)
        log_file = tmp_path / "logs" / "monitor" / "2026-06-26.md"
        content = log_file.read_text()
        assert "SUMMARY_GENERATED" in content
        assert "activity_003.md" in content

    def test_appends_to_existing(self, tmp_path):
        ml = MonitorLogger(str(tmp_path))
        ml.log_screenshot("2026-06-26", "10:00:15", "Chrome", "Page1", 100)
        ml.log_screenshot("2026-06-26", "10:00:30", "Chrome", "Page2", 200)
        content = (tmp_path / "logs" / "monitor" / "2026-06-26.md").read_text()
        assert content.count("SCREENSHOT") == 2


class TestChatLogger:
    def test_log_conversation(self, tmp_path):
        cl = ChatLogger(str(tmp_path))
        cl.log_conversation(
            date="2026-06-26",
            time="10:15:23",
            session_id="abc123",
            user_message="今天做了什么",
            assistant_response="你上午阅读了K8s文档",
            duration_sec=2.6,
            model="Qwen3.7-Max",
        )
        log_file = tmp_path / "logs" / "chat" / "2026-06-26.md"
        assert log_file.exists()
        content = log_file.read_text()
        assert "abc123" in content
        assert "今天做了什么" in content
        assert "2.6" in content


class TestStatsCollector:
    def test_flush_creates_json(self, tmp_path):
        sc = StatsCollector(str(tmp_path))
        sc.record_screenshot()
        sc.record_screenshot()
        sc.record_state_transition("IDLE", "OBSERVING")
        sc.record_engaged_session(240.0)
        sc.record_summary()
        sc.record_llm_call(3.2)
        sc.record_chat(2.6, ["read_activity_index"])
        sc.flush("2026-06-26")
        stats_file = tmp_path / "logs" / "stats" / "2026-06-26.json"
        assert stats_file.exists()
        data = json.loads(stats_file.read_text())
        assert data["monitor"]["screenshots_total"] == 2
        assert data["monitor"]["state_transitions"]["idle_to_observing"] == 1
        assert data["monitor"]["engaged_sessions"] == 1
        assert data["monitor"]["summaries_generated"] == 1
        assert data["chat"]["messages_total"] == 1

    def test_flush_resets_counters(self, tmp_path):
        sc = StatsCollector(str(tmp_path))
        sc.record_screenshot()
        sc.flush("2026-06-26")
        sc.flush("2026-06-27")
        data = json.loads((tmp_path / "logs" / "stats" / "2026-06-27.json").read_text())
        assert data["monitor"]["screenshots_total"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3.11 -m pytest tests/test_pet_logger.py -v`
Expected: ModuleNotFoundError

- [ ] **Step 3: Write implementation**

```python
# logs/__init__.py
# (empty)
```

```python
# logs/pet_logger.py
from __future__ import annotations

import json
from pathlib import Path


class MonitorLogger:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)

    def _append(self, date: str, line: str):
        log_dir = self._base_dir / "logs" / "monitor"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{date}.md"
        if not log_file.exists():
            log_file.write_text(f"# {date} 监控日志\n\n", encoding="utf-8")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def log_screenshot(self, date: str, time: str, app: str, title: str, ocr_len: int):
        self._append(date, f"- [{time}] SCREENSHOT app={app} title=\"{title}\" ocr_len={ocr_len}")

    def log_state_transition(self, date: str, time: str, from_state: str, to_state: str, reason: str = ""):
        reason_str = f" reason=\"{reason}\"" if reason else ""
        self._append(date, f"- [{time}] STATE {from_state} → {to_state}{reason_str}")

    def log_summary_generated(self, date: str, time: str, activity_file: str, ocr_inputs: int, llm_time: float):
        self._append(date, f"- [{time}] SUMMARY_GENERATED activity={activity_file} ocr_inputs={ocr_inputs} llm_time={llm_time:.1f}s")


class ChatLogger:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)

    def log_conversation(
        self,
        date: str,
        time: str,
        session_id: str,
        user_message: str,
        assistant_response: str,
        duration_sec: float,
        model: str = "",
    ):
        log_dir = self._base_dir / "logs" / "chat"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{date}.md"
        if not log_file.exists():
            log_file.write_text(f"# {date} 对话日志\n\n", encoding="utf-8")

        entry = (
            f"## {time} session={session_id}\n\n"
            f"**用户**: {user_message}\n\n"
            f"**助手**: {assistant_response}\n\n"
            f"- 耗时: {duration_sec:.1f}s\n"
        )
        if model:
            entry += f"- 模型: {model}\n"
        entry += "\n---\n\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)


class StatsCollector:
    def __init__(self, base_dir: str):
        self._base_dir = Path(base_dir)
        self._reset()

    def _reset(self):
        self._screenshots = 0
        self._transitions: dict[str, int] = {}
        self._engaged_sessions = 0
        self._engaged_durations: list[float] = []
        self._browsing_sessions = 0
        self._summaries = 0
        self._llm_calls = 0
        self._llm_times: list[float] = []
        self._chat_messages = 0
        self._chat_times: list[float] = []
        self._tools_used: dict[str, int] = {}

    def record_screenshot(self):
        self._screenshots += 1

    def record_state_transition(self, from_state: str, to_state: str):
        key = f"{from_state.lower()}_to_{to_state.lower()}"
        self._transitions[key] = self._transitions.get(key, 0) + 1
        if to_state == "ENGAGED":
            self._engaged_sessions += 1
        elif to_state == "BROWSING":
            self._browsing_sessions += 1

    def record_engaged_session(self, duration: float):
        self._engaged_durations.append(duration)

    def record_summary(self):
        self._summaries += 1

    def record_llm_call(self, duration: float):
        self._llm_calls += 1
        self._llm_times.append(duration)

    def record_chat(self, response_time: float, tools: list[str] | None = None):
        self._chat_messages += 1
        self._chat_times.append(response_time)
        for t in (tools or []):
            self._tools_used[t] = self._tools_used.get(t, 0) + 1

    def flush(self, date: str):
        stats_dir = self._base_dir / "logs" / "stats"
        stats_dir.mkdir(parents=True, exist_ok=True)

        avg_engaged = (
            sum(self._engaged_durations) / len(self._engaged_durations)
            if self._engaged_durations else 0
        )
        avg_llm = (
            sum(self._llm_times) / len(self._llm_times)
            if self._llm_times else 0
        )
        avg_chat = (
            sum(self._chat_times) / len(self._chat_times)
            if self._chat_times else 0
        )

        data = {
            "date": date,
            "monitor": {
                "screenshots_total": self._screenshots,
                "state_transitions": dict(self._transitions),
                "engaged_sessions": self._engaged_sessions,
                "engaged_avg_duration_sec": round(avg_engaged, 1),
                "browsing_sessions": self._browsing_sessions,
                "summaries_generated": self._summaries,
                "llm_calls_total": self._llm_calls,
                "llm_avg_time_sec": round(avg_llm, 1),
            },
            "chat": {
                "messages_total": self._chat_messages,
                "avg_response_time_sec": round(avg_chat, 1),
                "tools_used": dict(self._tools_used),
            },
        }

        stats_file = stats_dir / f"{date}.json"
        stats_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        self._reset()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3.11 -m pytest tests/test_pet_logger.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add logs/__init__.py logs/pet_logger.py tests/test_pet_logger.py
git commit -m "feat: add three-tier pet logger (monitor, chat, stats)"
```

---

### Task 5: Rewrite screen_monitor.py

**Files:**
- Modify: `monitor/screen_monitor.py` (full rewrite)
- Modify: `monitor/llm_client.py` (accept `list[str]` instead of single `str`)
- Test: `tests/test_screen_monitor.py` (update for new interfaces)

**Interfaces:**
- Consumes:
  - `BehaviorStateMachine.process(scene, ocr_text, timestamp) -> StateAction` from Task 3
  - `save_ocr(base_dir, date, timestamp, text) -> str` from Task 2
  - `MonitorLogger`, `StatsCollector` from Task 4
  - `generate_summary(ocr_texts: list[str], window_title, scene_type, ...) -> tuple[str, str]` (modified signature)
- Produces: Updated `ScreenMonitor` class — used by `app/main.py` (Task 7)

- [ ] **Step 1: Update `generate_summary` to accept OCR text list**

Change `monitor/llm_client.py` — the `ocr_text: str` parameter becomes `ocr_texts: list[str]`. The function deduplicates and merges them before sending to LLM.

```python
# monitor/llm_client.py
from __future__ import annotations

import requests


def _dedupe_ocr_texts(texts: list[str], max_chars: int = 3000) -> str:
    seen = set()
    unique = []
    for t in texts:
        t_stripped = t.strip()
        if t_stripped and t_stripped not in seen:
            seen.add(t_stripped)
            unique.append(t_stripped)
    merged = "\n---\n".join(unique)
    return merged[:max_chars]


def generate_summary(
    ocr_texts: list[str],
    window_title: str,
    scene_type: str,
    duration_sec: float = 0,
    base_url: str = "http://localhost:11434",
    model: str = "qwen3:8b",
) -> tuple[str, str]:
    scene_label = "阅读文章/文档" if scene_type == "reading" else "编写文档"

    system_prompt = (
        "你是一个屏幕活动记录助手。你的任务是根据用户屏幕截图的OCR文字内容，"
        "准确记录用户当前正在做什么以及文档/文章的核心内容。\n"
        "要求：\n"
        "- 摘要要具体，提取实际的文章标题、代码项目名、文档主题等关键信息\n"
        "- 内容要点必须提取文档中的关键概念、论点、数据、结论等实质性内容\n"
        "- 不要编造内容，只基于OCR文字推断\n"
        "- 如果OCR文字质量差或无法判断，如实说明\n"
        "- 直接输出结果，不要输出思考过程\n"
        "- 严格按照指定格式输出"
    )

    merged_ocr = _dedupe_ocr_texts(ocr_texts)
    duration_min = int(duration_sec // 60)

    prompt = (
        f"用户正在{scene_label}，持续了约{duration_min}分钟。\n"
        f"窗口标题：{window_title}\n"
        f"页面内容（多次OCR识别合并）：\n{merged_ocr}\n\n"
        f"请生成三部分内容：\n"
        f"1. 一句话摘要（20字以内，说明用户在做什么）\n"
        f"2. 内容要点（提取文档/文章中的核心内容，列出3-5个要点，每个要点一行）\n"
        f"3. 详细描述（100-200字，描述用户在做什么，文档主题是什么，"
        f"涉及哪些关键概念或技术点）\n\n"
        f"格式：\n"
        f"摘要：...\n"
        f"要点：\n- ...\n- ...\n- ...\n"
        f"详细：..."
    )

    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "system": system_prompt, "prompt": prompt, "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "")

        summary = ""
        key_points = []
        detail = ""
        current_section = None

        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("摘要：") or stripped.startswith("摘要:"):
                summary = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
                current_section = None
            elif stripped.startswith("要点：") or stripped.startswith("要点:"):
                current_section = "points"
            elif stripped.startswith("详细：") or stripped.startswith("详细:"):
                detail = stripped.split("：", 1)[-1].split(":", 1)[-1].strip()
                current_section = "detail"
            elif current_section == "points" and stripped.startswith("- "):
                key_points.append(stripped)
            elif current_section == "detail" and stripped:
                detail += stripped

        if not summary:
            summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"

        content_parts = []
        if key_points:
            content_parts.append("### 内容要点\n")
            content_parts.append("\n".join(key_points))
        if detail:
            content_parts.append("\n\n### 详细描述\n")
            content_parts.append(detail)

        full_content = "\n".join(content_parts) if content_parts else f"用户在{window_title}中进行了{scene_label}活动。"

        return summary, full_content
    except Exception:
        summary = f"{'阅读' if scene_type == 'reading' else '编写'}了{window_title}"
        full_content = f"用户在{window_title}中进行了{scene_label}活动。"
        return summary, full_content
```

- [ ] **Step 2: Rewrite `screen_monitor.py`**

```python
# monitor/screen_monitor.py
from __future__ import annotations

import logging
import os
import threading
import time
from datetime import datetime

from monitor.screenshot import capture_foreground_window
from monitor.idle_detector import is_user_idle
from monitor.ocr import recognize_text
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

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception:
                logger.exception("Monitor tick failed")
            self._stop_event.wait(self._interval)

    def _tick(self) -> None:
        if is_user_idle(self._idle_timeout):
            return

        image, title, process = capture_foreground_window()
        if image is None:
            return

        ocr_text = recognize_text(image)

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")
        ts_for_file = now.strftime("%H-%M-%S")
        timestamp_full = now.strftime("%Y-%m-%d %H:%M:%S")

        save_screenshot(image, self._base_dir, date_str, ts_for_file, quality=self._screenshot_quality)
        save_ocr(self._base_dir, date_str, ts_for_file, ocr_text)

        self._stats.record_screenshot()
        self._monitor_logger.log_screenshot(date_str, time_str, process, title, len(ocr_text))

        scene = classify_scene(title, process, ocr_text)

        old_state = self._state_machine.state
        action = self._state_machine.process(scene, ocr_text, timestamp_full)
        new_state = self._state_machine.state

        if old_state != new_state:
            self._monitor_logger.log_state_transition(date_str, time_str, old_state, new_state)
            self._stats.record_state_transition(old_state, new_state)

        if action.action == "generate_summary" and action.scene is not None:
            self._generate_and_write(action, date_str, time_str)

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
```

- [ ] **Step 3: Update tests**

```python
# tests/test_screen_monitor.py
from unittest.mock import patch, MagicMock
from monitor.screen_monitor import ScreenMonitor


def test_monitor_start_stop(tmp_path):
    monitor = ScreenMonitor(base_dir=str(tmp_path), interval=0.1, engage_threshold=2)
    monitor.start()
    assert monitor.is_running()
    monitor.stop()
    assert not monitor.is_running()


@patch("monitor.screen_monitor.capture_foreground_window")
@patch("monitor.screen_monitor.is_user_idle", return_value=False)
@patch("monitor.screen_monitor.recognize_text", return_value="test ocr content " * 10)
def test_tick_saves_screenshot_and_ocr(mock_ocr, mock_idle, mock_capture, tmp_path):
    from PIL import Image
    img = Image.new("RGB", (100, 100))
    mock_capture.return_value = (img, "Test Title", "Google Chrome")

    monitor = ScreenMonitor(base_dir=str(tmp_path), interval=60, engage_threshold=2)
    monitor._tick()

    screenshots = list((tmp_path / "screenshots").rglob("*.jpg"))
    assert len(screenshots) == 1
    ocr_files = list((tmp_path / "ocr").rglob("*.txt"))
    assert len(ocr_files) == 1
```

- [ ] **Step 4: Run tests**

Run: `python3.11 -m pytest tests/test_screen_monitor.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add monitor/screen_monitor.py monitor/llm_client.py tests/test_screen_monitor.py
git commit -m "feat: rewrite screen_monitor with behavior state machine"
```

---

### Task 6: Chat Logging in ClaudeClient

**Files:**
- Modify: `app/claude_client.py`
- Test: `tests/test_claude_client.py` (update)

**Interfaces:**
- Consumes: `ChatLogger`, `StatsCollector` from Task 4
- Produces: Updated `ClaudeClient` that logs every conversation

- [ ] **Step 1: Update `claude_client.py`**

```python
# app/claude_client.py
from __future__ import annotations

import json
import logging
import subprocess
import time
from datetime import datetime
from typing import Optional

from logs.pet_logger import ChatLogger, StatsCollector

logger = logging.getLogger(__name__)


class ClaudeClient:
    def __init__(
        self,
        project_dir: str | None = None,
        chat_logger: ChatLogger | None = None,
        stats_collector: StatsCollector | None = None,
    ):
        self._project_dir = project_dir
        self._session_id: str | None = None
        self._chat_logger = chat_logger
        self._stats = stats_collector

    def send_message(self, text: str) -> Optional[str]:
        cmd = ["claude", "-p", text, "--output-format", "json"]
        if self._session_id:
            cmd.extend(["--resume", self._session_id])

        start = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120, cwd=self._project_dir,
            )
            data = json.loads(result.stdout)

            if data.get("is_error"):
                error_msg = data.get("result", "Unknown error")
                logger.error("Claude Code error: %s", error_msg)
                return f"[错误] {error_msg}"

            self._session_id = data.get("session_id", self._session_id)
            response = data.get("result", "")
            duration = time.time() - start

            model = ""
            model_usage = data.get("modelUsage", {})
            if model_usage:
                model = next(iter(model_usage.keys()), "")

            self._log(text, response, duration, model)
            return response

        except subprocess.TimeoutExpired:
            logger.error("Claude Code timed out")
            return None
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude Code output: %s", e)
            return None
        except FileNotFoundError:
            logger.error("Claude Code CLI not found")
            return None
        except Exception:
            logger.exception("Failed to call Claude Code")
            return None

    def _log(self, user_msg: str, response: str, duration: float, model: str):
        now = datetime.now()
        if self._chat_logger:
            self._chat_logger.log_conversation(
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                session_id=self._session_id or "unknown",
                user_message=user_msg,
                assistant_response=response[:500],
                duration_sec=duration,
                model=model,
            )
        if self._stats:
            self._stats.record_chat(duration)

    def is_connected(self) -> bool:
        try:
            result = subprocess.run(
                ["claude", "-p", "hi", "--output-format", "json", "--max-turns", "1"],
                capture_output=True, text=True, timeout=15,
            )
            data = json.loads(result.stdout)
            return not data.get("is_error", True)
        except Exception:
            return False

    def clear_conversation(self) -> None:
        self._session_id = None
```

- [ ] **Step 2: Update test**

```python
# tests/test_claude_client.py
from unittest.mock import patch, MagicMock
from app.claude_client import ClaudeClient


@patch("app.claude_client.subprocess.run")
def test_send_message_logs_chat(mock_run, tmp_path):
    mock_run.return_value = MagicMock(
        stdout='{"result":"ok","session_id":"s1","is_error":false,"modelUsage":{"Qwen":{}}}',
        returncode=0,
    )
    from logs.pet_logger import ChatLogger, StatsCollector
    chat_logger = ChatLogger(str(tmp_path))
    stats = StatsCollector(str(tmp_path))
    client = ClaudeClient(chat_logger=chat_logger, stats_collector=stats)
    result = client.send_message("hello")
    assert result == "ok"
    log_files = list((tmp_path / "logs" / "chat").rglob("*.md"))
    assert len(log_files) == 1


@patch("app.claude_client.subprocess.run")
def test_send_message_without_logger(mock_run):
    mock_run.return_value = MagicMock(
        stdout='{"result":"ok","session_id":"s1","is_error":false}',
        returncode=0,
    )
    client = ClaudeClient()
    result = client.send_message("hello")
    assert result == "ok"
```

- [ ] **Step 3: Run tests**

Run: `python3.11 -m pytest tests/test_claude_client.py -v`
Expected: all PASS

- [ ] **Step 4: Commit**

```bash
git add app/claude_client.py tests/test_claude_client.py
git commit -m "feat: add chat logging to ClaudeClient"
```

---

### Task 7: Config, Cleanup, and main.py Integration

**Files:**
- Modify: `config.yaml`
- Modify: `memory/screenshot_cleaner.py` (add `cleanup_logs_expired`)
- Modify: `app/main.py` (wire everything together)
- Test: `tests/test_screenshot_cleaner.py` (add log cleanup test)

**Interfaces:**
- Consumes: all modules from Tasks 1-6
- Produces: fully integrated app entry point

- [ ] **Step 1: Update `config.yaml`**

```yaml
monitor:
  enabled: true
  interval_seconds: 15
  scenes:
    - reading
    - writing
  idle_timeout_seconds: 120
  engage_threshold: 5

screenshots:
  quality: 75
  cleanup_similarity: 0.9
  retention_days: 7

ocr:
  engine: paddleocr
  lang: ch
  retention_days: 7

llm:
  local:
    provider: ollama
    model: qwen3:8b
    base_url: http://localhost:11434

logs:
  retention_days: 30

memory:
  base_dir: ~/.pet-memory
  embedding_model: bge-small-zh

ui:
  window_width: 400
  window_height: 600
```

- [ ] **Step 2: Add `cleanup_logs_expired` to `screenshot_cleaner.py`**

Append to end of file:

```python
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
```

- [ ] **Step 3: Write test for log cleanup**

Add to `tests/test_screenshot_cleaner.py`:

```python
from memory.screenshot_cleaner import cleanup_logs_expired


def test_cleanup_logs_expired(tmp_path):
    monitor_dir = tmp_path / "logs" / "monitor"
    monitor_dir.mkdir(parents=True)
    (monitor_dir / "2020-01-01.md").write_text("old log")
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    (monitor_dir / f"{today}.md").write_text("today log")

    removed = cleanup_logs_expired(str(tmp_path), retention_days=30)
    assert removed == 1
    assert not (monitor_dir / "2020-01-01.md").exists()
    assert (monitor_dir / f"{today}.md").exists()
```

- [ ] **Step 4: Rewrite `app/main.py`**

```python
# app/main.py
from __future__ import annotations

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, pyqtSignal

from app.config import load_config
from app.claude_client import ClaudeClient
from monitor.screen_monitor import ScreenMonitor
from memory.summary_generator import SummaryGenerator
from logs.pet_logger import ChatLogger, StatsCollector
from ui.main_window import MainWindow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

MEMORY_DIR = os.path.expanduser("~/.pet-memory")


class ChatWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client: ClaudeClient, message: str):
        super().__init__()
        self._client = client
        self._message = message

    def run(self):
        response = self._client.send_message(self._message)
        if response:
            self.response_ready.emit(response)
        else:
            self.error_occurred.emit("获取回复失败，请确认 Claude Code 已登录。")


class PetApp:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
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
            stats_collector=self._stats,
        )
        self._summary_gen = SummaryGenerator(
            base_dir=MEMORY_DIR,
            llm_base_url=self._config["llm"]["local"]["base_url"],
            llm_model=self._config["llm"]["local"]["model"],
        )
        self._window: MainWindow | None = None
        self._health_timer: QTimer | None = None
        self._chat_worker: ChatWorker | None = None

    def run(self):
        app = QApplication(sys.argv)

        self._window = MainWindow(
            on_message_sent=self._on_user_message,
            width=self._config["ui"]["window_width"],
            height=self._config["ui"]["window_height"],
        )

        self._start_services()
        self._window.show()

        self._health_timer = QTimer()
        self._health_timer.timeout.connect(self._check_health)
        self._health_timer.start(30000)

        exit_code = app.exec()
        self._shutdown()
        sys.exit(exit_code)

    def _start_services(self):
        if self._window:
            self._window.status_bar.set_hermes_status(True)
            self._window.chat_widget.append_message(
                "system", "逗叽脑袋已启动，对话将通过 Claude Code 处理。"
            )

        if self._config["monitor"]["enabled"]:
            self._monitor.start()
            if self._window:
                self._window.status_bar.set_monitor_status(True)

        self._summary_gen.check_and_generate_pending()

    def _on_user_message(self, text: str):
        if self._window:
            self._window.chat_widget.set_input_enabled(False)

        self._chat_worker = ChatWorker(self._client, text)
        self._chat_worker.response_ready.connect(self._on_response)
        self._chat_worker.error_occurred.connect(self._on_error)
        self._chat_worker.start()

    def _on_response(self, response: str):
        if self._window:
            self._window.chat_widget.append_message("assistant", response)
            self._window.chat_widget.set_input_enabled(True)

    def _on_error(self, error: str):
        if self._window:
            self._window.chat_widget.append_message("system", error)
            self._window.chat_widget.set_input_enabled(True)

    def _check_health(self):
        monitor_ok = self._monitor.is_running()
        if self._window:
            self._window.status_bar.set_monitor_status(monitor_ok)

    def _shutdown(self):
        logger.info("Shutting down...")
        self._monitor.stop()

        from datetime import datetime
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
    app = PetApp()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run all tests**

Run: `python3.11 -m pytest tests/ -v --ignore=tests/test_activity_merger.py`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add config.yaml memory/screenshot_cleaner.py app/main.py tests/test_screenshot_cleaner.py
git commit -m "feat: integrate state machine, logging, and cleanup into app"
```

---

### Task 8: Clean Up Stale References

**Files:**
- Modify: `tests/test_integration.py` (update imports from `ActivityMerger` → `BehaviorStateMachine`)
- Modify: `tests/test_app_main.py` (update for new `ScreenMonitor` constructor)
- Modify: any file still importing `activity_merger`

**Interfaces:**
- Consumes: all prior tasks
- Produces: clean, passing test suite

- [ ] **Step 1: Find all references to `activity_merger`**

Run: `grep -rn "activity_merger\|ActivityMerger\|confirm_count" --include="*.py" .`

Update each file to use `BehaviorStateMachine` / `engage_threshold` instead.

- [ ] **Step 2: Run full test suite**

Run: `python3.11 -m pytest tests/ -v`
Expected: all PASS, zero import errors

- [ ] **Step 3: Run the app manually**

Run: `python3.11 -m app.main`
Verify: window opens, monitor starts, no tracebacks in console.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: clean up stale ActivityMerger references"
```
