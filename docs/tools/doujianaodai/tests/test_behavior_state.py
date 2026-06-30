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
