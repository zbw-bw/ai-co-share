from monitor.scene_classifier import classify_scene, SceneResult


def test_classify_reading_chrome():
    result = classify_scene(
        window_title="LangGraph教程 - 掘金",
        process_name="Google Chrome",
        ocr_text="LangGraph 是一个用于构建有状态多角色应用的框架。" * 10,
    )
    assert result.scene_type == "reading"
    assert "LangGraph教程" in result.title


def test_classify_writing_word():
    result = classify_scene(
        window_title="产品需求文档.docx",
        process_name="Microsoft Word",
        ocr_text="1. 功能概述\n2. 用户故事\n3. 技术方案",
    )
    assert result.scene_type == "writing"
    assert "产品需求文档" in result.title


def test_classify_skip_unknown_app():
    result = classify_scene(
        window_title="Steam",
        process_name="Steam",
        ocr_text="Play games",
    )
    assert result.scene_type is None


def test_classify_reading_needs_enough_text():
    result = classify_scene(
        window_title="Google Chrome",
        process_name="Google Chrome",
        ocr_text="Hi",
    )
    assert result.scene_type is None


def test_classify_writing_pages():
    result = classify_scene(
        window_title="报告",
        process_name="Pages",
        ocr_text="本季度工作总结\n一、项目进展\n二、存在问题",
    )
    assert result.scene_type == "writing"
