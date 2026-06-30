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
