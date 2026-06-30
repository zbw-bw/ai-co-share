from __future__ import annotations

import base64
import io
import re
import numpy as np
import requests
from PIL import Image, ImageEnhance, ImageFilter


def _preprocess(image: Image.Image) -> Image.Image:
    if image.width > 1920:
        ratio = 1920 / image.width
        image = image.resize((1920, int(image.height * ratio)), Image.LANCZOS)
    image = image.convert("L")
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)
    return image.convert("RGB")


def _dhash(image: Image.Image, size: int = 16) -> bytes:
    resized = image.convert("L").resize((size + 1, size), Image.LANCZOS)
    arr = np.array(resized)
    diff = arr[:, 1:] > arr[:, :-1]
    return diff.flatten().tobytes()


def image_similarity(hash_a: bytes, hash_b: bytes) -> float:
    if not hash_a or not hash_b or len(hash_a) != len(hash_b):
        return 0.0
    bits_diff = sum(a != b for a, b in zip(hash_a, hash_b))
    return 1 - bits_diff / len(hash_a)


_GARBLE_RE = re.compile(r"[^一-鿿　-〿a-zA-Z0-9\s，。、；：！？""''（）《》【】\-+=/%.@#&*·—…·—…，．：；！？]")


def _clean_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if len(line) < 2:
        return ""
    garble_chars = len(_GARBLE_RE.findall(line))
    total_chars = len(line)
    if total_chars > 0 and garble_chars / total_chars > 0.4:
        return ""
    if re.fullmatch(r"[a-zA-Z0-9+/=_\-]{16,}", line):
        return ""
    if total_chars > 4 and sum(1 for c in line if c.isdigit()) / total_chars > 0.6:
        return ""
    line = _GARBLE_RE.sub("", line)
    return line.strip()


def _sort_and_clean(result: list, score_threshold: float = 0.3) -> str:
    blocks = []
    for item in result:
        texts = item.get("rec_texts", [])
        scores = item.get("rec_scores", [])
        polys = item.get("dt_polys", [])
        for i, (text, score) in enumerate(zip(texts, scores)):
            if score < score_threshold:
                continue
            if i < len(polys):
                poly = polys[i]
                y = min(p[1] for p in poly)
                x = min(p[0] for p in poly)
            else:
                y, x = 0, 0
            blocks.append((y, x, text))

    blocks.sort(key=lambda b: (b[0] // 20, b[1]))

    lines = []
    for _, _, text in blocks:
        cleaned = _clean_line(text)
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def _image_to_base64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


class PaddleOcrEngine:
    def __init__(self, lang: str = "ch"):
        from paddleocr import PaddleOCR
        import logging
        logging.getLogger("ppocr").setLevel(logging.WARNING)
        self._ocr = PaddleOCR(lang=lang, use_textline_orientation=True)

    def recognize(self, image: Image.Image) -> str:
        processed = _preprocess(image)
        img_array = np.array(processed)
        result = self._ocr.predict(img_array)
        return _sort_and_clean(result)


class OllamaVisionEngine:
    def __init__(self, model: str = "minicpm-v", base_url: str = "http://localhost:11434"):
        self._model = model
        self._base_url = base_url

    def recognize(self, image: Image.Image) -> str:
        if image.width > 1920:
            ratio = 1920 / image.width
            image = image.resize((1920, int(image.height * ratio)), Image.LANCZOS)

        img_b64 = _image_to_base64(image)
        prompt = (
            "请仔细识别这张屏幕截图中的所有文字内容。"
            "按照从上到下、从左到右的阅读顺序输出。"
            "只输出识别到的文字，不要描述图片、不要解释、不要加任何额外内容。"
        )
        try:
            resp = requests.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "images": [img_b64],
                    "stream": False,
                },
                timeout=120,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "")
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Ollama vision OCR failed: %s", e)
            return ""


class OcrEngine:
    SKIP_THRESHOLD = 0.70

    def __init__(self, engine_type: str = "paddleocr", lang: str = "ch",
                 vision_model: str = "minicpm-v", ollama_url: str = "http://localhost:11434"):
        self._last_hash: bytes = b""
        self._last_text: str = ""
        self._engine_type = engine_type

        if engine_type == "ollama_vision":
            self._backend = OllamaVisionEngine(model=vision_model, base_url=ollama_url)
        else:
            self._backend = PaddleOcrEngine(lang=lang)

    def recognize(self, image: Image.Image) -> tuple[str, bool]:
        current_hash = _dhash(image)

        if self._last_hash:
            sim = image_similarity(self._last_hash, current_hash)
            if sim >= self.SKIP_THRESHOLD:
                return self._last_text, True

        text = self._backend.recognize(image)

        self._last_hash = current_hash
        self._last_text = text
        return text, False


_engine: OcrEngine | None = None


def init_engine(engine_type: str = "paddleocr", lang: str = "ch",
                vision_model: str = "minicpm-v", ollama_url: str = "http://localhost:11434"):
    global _engine
    _engine = OcrEngine(engine_type=engine_type, lang=lang,
                        vision_model=vision_model, ollama_url=ollama_url)


def recognize_text(image: Image.Image, lang: str = "ch") -> str:
    global _engine
    if _engine is None:
        _engine = OcrEngine(lang=lang)
    text, _ = _engine.recognize(image)
    return text


def recognize_text_with_skip(image: Image.Image, lang: str = "ch") -> tuple[str, bool]:
    global _engine
    if _engine is None:
        _engine = OcrEngine(lang=lang)
    return _engine.recognize(image)
