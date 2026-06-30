# ui/settings_widget.py
from __future__ import annotations

import os
from pathlib import Path

import requests
import yaml
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QSlider, QSpinBox, QPushButton, QCheckBox, QHBoxLayout,
)
from PyQt6.QtCore import Qt


class SettingsWidget(QWidget):
    def __init__(self, config: dict, config_path: str, on_config_changed: callable, parent=None):
        super().__init__(parent)
        self._config = config
        self._config_path = config_path
        self._on_config_changed = on_config_changed
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("⚙️ 设置")
        header.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(header)

        form = QFormLayout()
        form.setSpacing(12)

        self._model_combo = QComboBox()
        self._refresh_models()
        refresh_btn = QPushButton("刷新")
        refresh_btn.setFixedWidth(50)
        refresh_btn.clicked.connect(self._refresh_models)
        model_row = QHBoxLayout()
        model_row.addWidget(self._model_combo, stretch=1)
        model_row.addWidget(refresh_btn)
        form.addRow("Ollama 模型", model_row)

        self._interval_slider = QSlider(Qt.Orientation.Horizontal)
        self._interval_slider.setRange(10, 60)
        self._interval_slider.setValue(self._config["monitor"]["interval_seconds"])
        self._interval_label = QLabel(f"{self._interval_slider.value()}s")
        self._interval_slider.valueChanged.connect(lambda v: self._interval_label.setText(f"{v}s"))
        interval_row = QHBoxLayout()
        interval_row.addWidget(self._interval_slider, stretch=1)
        interval_row.addWidget(self._interval_label)
        form.addRow("截图间隔", interval_row)

        self._threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self._threshold_slider.setRange(3, 10)
        self._threshold_slider.setValue(self._config["monitor"]["engage_threshold"])
        self._threshold_label = QLabel(f"{self._threshold_slider.value()} 次")
        self._threshold_slider.valueChanged.connect(lambda v: self._threshold_label.setText(f"{v} 次"))
        threshold_row = QHBoxLayout()
        threshold_row.addWidget(self._threshold_slider, stretch=1)
        threshold_row.addWidget(self._threshold_label)
        form.addRow("深度活动阈值", threshold_row)

        self._screenshot_days = QSpinBox()
        self._screenshot_days.setRange(1, 90)
        self._screenshot_days.setValue(self._config["screenshots"]["retention_days"])
        form.addRow("截图保留天数", self._screenshot_days)

        self._ocr_days = QSpinBox()
        self._ocr_days.setRange(1, 90)
        self._ocr_days.setValue(self._config.get("ocr", {}).get("retention_days", 7))
        form.addRow("OCR 保留天数", self._ocr_days)

        self._log_days = QSpinBox()
        self._log_days.setRange(1, 365)
        self._log_days.setValue(self._config.get("logs", {}).get("retention_days", 30))
        form.addRow("日志保留天数", self._log_days)

        self._ocr_engine_combo = QComboBox()
        self._ocr_engine_combo.addItems(["paddleocr", "ollama_vision"])
        current_engine = self._config.get("ocr", {}).get("engine", "paddleocr")
        idx = self._ocr_engine_combo.findText(current_engine)
        if idx >= 0:
            self._ocr_engine_combo.setCurrentIndex(idx)
        form.addRow("OCR 引擎", self._ocr_engine_combo)

        self._vision_model_combo = QComboBox()
        self._vision_model_combo.setEditable(True)
        self._vision_model_combo.addItems(["minicpm-v", "moondream", "llava", "glm-ocr"])
        current_vm = self._config.get("ocr", {}).get("vision_model", "minicpm-v")
        vm_idx = self._vision_model_combo.findText(current_vm)
        if vm_idx >= 0:
            self._vision_model_combo.setCurrentIndex(vm_idx)
        else:
            self._vision_model_combo.setCurrentText(current_vm)
        form.addRow("视觉模型", self._vision_model_combo)

        layout.addLayout(form)
        layout.addStretch()

        save_btn = QPushButton("保存设置")
        save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 6px; padding: 10px; font-size: 14px; }"
        )
        save_btn.clicked.connect(self._save)
        layout.addWidget(save_btn)

    def _refresh_models(self):
        self._model_combo.clear()
        base_url = self._config["llm"]["local"]["base_url"]
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                self._model_combo.addItems(models)
                current = self._config["llm"]["local"]["model"]
                idx = self._model_combo.findText(current)
                if idx >= 0:
                    self._model_combo.setCurrentIndex(idx)
        except Exception:
            self._model_combo.addItem(self._config["llm"]["local"]["model"])

    def _save(self):
        if not os.path.exists(self._config_path):
            config_data = {}
        else:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

        config_data.setdefault("monitor", {})["interval_seconds"] = self._interval_slider.value()
        config_data["monitor"]["engage_threshold"] = self._threshold_slider.value()
        config_data.setdefault("screenshots", {})["retention_days"] = self._screenshot_days.value()
        config_data.setdefault("ocr", {})["retention_days"] = self._ocr_days.value()
        config_data["ocr"]["engine"] = self._ocr_engine_combo.currentText()
        config_data["ocr"]["vision_model"] = self._vision_model_combo.currentText()
        config_data.setdefault("logs", {})["retention_days"] = self._log_days.value()
        model = self._model_combo.currentText()
        if model:
            config_data.setdefault("llm", {}).setdefault("local", {})["model"] = model

        with open(self._config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)

        from app.config import load_config
        new_config = load_config(self._config_path)
        self._config = new_config
        self._on_config_changed(new_config)
