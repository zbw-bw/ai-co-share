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
