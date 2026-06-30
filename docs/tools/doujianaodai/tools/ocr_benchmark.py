#!/usr/bin/env python3
"""OCR 引擎效果评测工具。

用法:
  python3 tools/ocr_benchmark.py <截图路径>
  python3 tools/ocr_benchmark.py ~/.pet-memory/screenshots/2026-06-29/14-14-35.jpg

对比引擎: PaddleOCR、Ollama 视觉模型、外部 API（可选）
"""
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import sys
import time

import requests
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def run_paddleocr(image: Image.Image) -> tuple[str, float]:
    from monitor.ocr import PaddleOcrEngine
    engine = PaddleOcrEngine(lang="ch")
    start = time.time()
    text = engine.recognize(image)
    return text, time.time() - start


def run_ollama_vision(image: Image.Image, model: str, base_url: str = "http://localhost:11434") -> tuple[str, float]:
    if image.width > 1920:
        ratio = 1920 / image.width
        image = image.resize((1920, int(image.height * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    prompt = (
        "请仔细识别这张屏幕截图中的所有文字内容。"
        "按照从上到下、从左到右的阅读顺序输出。"
        "只输出识别到的文字，不要描述图片。"
    )
    start = time.time()
    try:
        resp = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "images": [img_b64], "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        import re
        text = resp.json().get("response", "")
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return text, time.time() - start
    except Exception as e:
        return f"[ERROR] {e}", time.time() - start


def run_api_vision(image: Image.Image, api_url: str, api_key: str, model: str) -> tuple[str, float]:
    if image.width > 1920:
        ratio = 1920 / image.width
        image = image.resize((1920, int(image.height * ratio)), Image.LANCZOS)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    start = time.time()
    try:
        resp = requests.post(
            f"{api_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {"type": "base64", "media_type": "image/png", "data": img_b64},
                        },
                        {
                            "type": "text",
                            "text": "请仔细识别这张屏幕截图中的所有文字内容，按从上到下从左到右顺序输出。只输出文字，不要描述图片。",
                        },
                    ],
                }],
            },
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        return text, time.time() - start
    except Exception as e:
        return f"[ERROR] {e}", time.time() - start


def score_quality(text: str) -> dict:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    total_chars = sum(len(l) for l in lines)
    cn_chars = sum(1 for c in text if "一" <= c <= "鿿")
    en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    garble = total_chars - cn_chars - en_chars - sum(1 for c in text if c.isdigit() or c.isspace() or c in "，。、：；！？""''（）《》【】-+=/%.@#&*·")
    return {
        "lines": len(lines),
        "chars": total_chars,
        "chinese": cn_chars,
        "english": en_chars,
        "garble_ratio": f"{garble / total_chars:.1%}" if total_chars else "N/A",
    }


def main():
    parser = argparse.ArgumentParser(description="OCR 引擎评测")
    parser.add_argument("image", help="截图路径")
    parser.add_argument("--ollama-model", default="minicpm-v", help="Ollama 视觉模型名")
    parser.add_argument("--api-url", default="", help="外部 API URL（如 idealab）")
    parser.add_argument("--api-key", default="", help="外部 API Key")
    parser.add_argument("--api-model", default="", help="外部 API 模型名")
    parser.add_argument("--skip-paddle", action="store_true", help="跳过 PaddleOCR")
    parser.add_argument("--skip-ollama", action="store_true", help="跳过 Ollama")
    args = parser.parse_args()

    image = Image.open(os.path.expanduser(args.image))
    print(f"截图: {args.image} ({image.size[0]}x{image.size[1]})")
    print("=" * 60)

    results = {}

    if not args.skip_paddle:
        print("\n⏳ PaddleOCR 识别中...")
        text, elapsed = run_paddleocr(image)
        results["PaddleOCR"] = (text, elapsed)
        quality = score_quality(text)
        print(f"✅ PaddleOCR: {elapsed:.1f}s | {quality['lines']}行 {quality['chars']}字 | 乱码率{quality['garble_ratio']}")
        print(f"--- 前300字 ---\n{text[:300]}\n")

    if not args.skip_ollama:
        # Check if model is available
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=3)
            models = [m["name"] for m in resp.json().get("models", [])]
            if args.ollama_model in models or any(args.ollama_model in m for m in models):
                print(f"⏳ Ollama ({args.ollama_model}) 识别中...")
                text, elapsed = run_ollama_vision(image, args.ollama_model)
                results[f"Ollama:{args.ollama_model}"] = (text, elapsed)
                quality = score_quality(text)
                print(f"✅ Ollama: {elapsed:.1f}s | {quality['lines']}行 {quality['chars']}字 | 乱码率{quality['garble_ratio']}")
                print(f"--- 前300字 ---\n{text[:300]}\n")
            else:
                print(f"⚠️ Ollama 模型 {args.ollama_model} 未安装，跳过。可用: {', '.join(models)}")
        except Exception:
            print("⚠️ Ollama 未运行，跳过。")

    if args.api_url and args.api_key and args.api_model:
        print(f"⏳ API ({args.api_model}) 识别中...")
        text, elapsed = run_api_vision(image, args.api_url, args.api_key, args.api_model)
        results[f"API:{args.api_model}"] = (text, elapsed)
        quality = score_quality(text)
        print(f"✅ API: {elapsed:.1f}s | {quality['lines']}行 {quality['chars']}字 | 乱码率{quality['garble_ratio']}")
        print(f"--- 前300字 ---\n{text[:300]}\n")

    if len(results) > 1:
        print("=" * 60)
        print("📊 对比总结")
        print(f"{'引擎':<25} {'耗时':>6} {'行数':>5} {'字数':>6} {'乱码率':>8}")
        for name, (text, elapsed) in results.items():
            q = score_quality(text)
            print(f"{name:<25} {elapsed:>5.1f}s {q['lines']:>5} {q['chars']:>6} {q['garble_ratio']:>8}")


if __name__ == "__main__":
    main()
