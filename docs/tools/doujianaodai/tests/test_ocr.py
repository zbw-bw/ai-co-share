from unittest.mock import patch, MagicMock
from PIL import Image
from monitor.ocr import recognize_text, OcrEngine, PaddleOcrEngine, _dhash


def test_recognize_text_returns_string():
    engine = OcrEngine.__new__(OcrEngine)
    engine._last_hash = b""
    engine._last_text = ""
    engine._engine_type = "paddleocr"
    mock_backend = MagicMock(spec=PaddleOcrEngine)
    mock_backend.recognize.return_value = "Hello World\n测试文本"
    engine._backend = mock_backend

    text, skipped = engine.recognize(Image.new("RGB", (200, 100)))
    assert "Hello World" in text
    assert "测试文本" in text
    assert skipped is False


def test_recognize_text_empty_image():
    engine = OcrEngine.__new__(OcrEngine)
    engine._last_hash = b""
    engine._last_text = ""
    engine._engine_type = "paddleocr"
    mock_backend = MagicMock(spec=PaddleOcrEngine)
    mock_backend.recognize.return_value = ""
    engine._backend = mock_backend

    text, skipped = engine.recognize(Image.new("RGB", (200, 100)))
    assert text == ""
    assert skipped is False


def test_recognize_text_skips_similar():
    engine = OcrEngine.__new__(OcrEngine)
    engine._last_text = "cached text"
    engine._engine_type = "paddleocr"
    mock_backend = MagicMock(spec=PaddleOcrEngine)
    engine._backend = mock_backend

    img = Image.new("RGB", (200, 100), color=(128, 128, 128))
    engine._last_hash = _dhash(img)

    text, skipped = engine.recognize(img)
    assert text == "cached text"
    assert skipped is True
    mock_backend.recognize.assert_not_called()
