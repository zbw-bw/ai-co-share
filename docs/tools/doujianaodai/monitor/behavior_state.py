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
