# app/preflight.py
from __future__ import annotations

import os
import subprocess
import sys

import requests
import yaml


def check_python() -> bool:
    return sys.version_info >= (3, 11)


def check_ollama(base_url: str = "http://localhost:11434") -> tuple[bool, list[str]]:
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            return True, models
    except Exception:
        pass
    return False, []


def check_claude_code() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return False, ""


def check_screen_capture() -> bool:
    try:
        from monitor.screenshot import capture_foreground_window
        img, _, _ = capture_foreground_window()
        return img is not None
    except Exception:
        return False


def select_model(models: list[str], current: str | None) -> str:
    if current and current in models:
        return current
    if not models:
        return ""
    print(f"    可用模型: {', '.join(models)}")
    default = models[0]
    choice = input(f"    ? 请选择用于活动摘要的模型 [{default}]: ").strip()
    return choice if choice in models else default


def _update_config_model(config_path: str, model: str):
    if not os.path.exists(config_path):
        config_data = {}
    else:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
    config_data.setdefault("llm", {}).setdefault("local", {})["model"] = model
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)


def run_preflight(config_path: str) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from app.config import load_config

    print("🔍 环境检查中...")

    if not check_python():
        print(f"[✗] Python {sys.version_info.major}.{sys.version_info.minor} — 需要 3.11+")
        sys.exit(1)
    print(f"[✓] Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    config = load_config(config_path)
    base_url = config["llm"]["local"]["base_url"]

    with ThreadPoolExecutor(max_workers=3) as pool:
        fut_ollama = pool.submit(check_ollama, base_url)
        fut_claude = pool.submit(check_claude_code)
        fut_screen = pool.submit(check_screen_capture)

        ollama_ok, models = fut_ollama.result()
        claude_ok, version = fut_claude.result()
        screen_ok = fut_screen.result()

    if not ollama_ok:
        print("[✗] Ollama 未运行")
        print("    安装: brew install ollama")
        print("    启动: ollama serve")
        sys.exit(1)
    print("[✓] Ollama 运行中")

    current_model = config["llm"]["local"]["model"]
    if current_model not in models:
        chosen = select_model(models, None)
        if not chosen:
            print("[✗] 没有可用的 Ollama 模型，请先运行: ollama pull qwen3:8b")
            sys.exit(1)
        _update_config_model(config_path, chosen)
        config = load_config(config_path)
        print(f"[✓] 模型已配置: {chosen}")
    else:
        print(f"[✓] 模型已配置: {current_model}")

    if not claude_ok:
        print("[✗] Claude Code 未找到")
        print("    安装: npm install -g @anthropic-ai/claude-code")
        sys.exit(1)
    print(f"[✓] Claude Code {version}")

    if screen_ok:
        print("[✓] 屏幕录制权限正常")
    else:
        print("[⚠] 屏幕录制权限未授权 — 请到 系统设置 > 隐私与安全 > 屏幕录制 中授权")

    print("✅ 启动逗叽脑袋...")
    return config
