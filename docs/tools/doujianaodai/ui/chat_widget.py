# ui/chat_widget.py
from __future__ import annotations

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _format_markdown(text: str) -> str:
    text = _escape_html(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r'<code style="background:#f0f0f0;padding:1px 4px;border-radius:3px;font-size:12px;">\1</code>', text)
    text = re.sub(r"^(\d+)\. ", r"<b>\1.</b> ", text, flags=re.MULTILINE)
    text = re.sub(r"^- ", "• ", text, flags=re.MULTILINE)
    text = text.replace("\n", "<br>")
    return text


class ChatWidget(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._reset_stream_state()

    def _reset_stream_state(self):
        self._current_thinking = False
        self._stream_start_pos = -1
        self._text_buffer: list[str] = []

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        header = QHBoxLayout()
        header.addWidget(QLabel("💬 聊天"))
        header.addStretch()
        self._clear_btn = QPushButton("清空对话")
        self._clear_btn.setStyleSheet("QPushButton { font-size: 12px; padding: 2px 8px; }")
        self._clear_btn.clicked.connect(self.clear_chat)
        header.addWidget(self._clear_btn)
        layout.addLayout(header)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setStyleSheet(
            "QTextEdit { background-color: #f5f5f5; border: 1px solid #ddd; "
            "border-radius: 8px; padding: 8px; font-size: 14px; }"
        )
        layout.addWidget(self._chat_display, stretch=1)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("QLabel { color: #888; font-size: 12px; }")
        layout.addWidget(self._status_label)

        input_layout = QHBoxLayout()
        self._input_field = QLineEdit()
        self._input_field.setPlaceholderText("输入消息...")
        self._input_field.setStyleSheet(
            "QLineEdit { border: 1px solid #ccc; border-radius: 6px; "
            "padding: 8px; font-size: 14px; }"
        )
        self._input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input_field, stretch=1)

        self._send_button = QPushButton("发送")
        self._send_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; "
            "border: none; border-radius: 6px; padding: 8px 16px; font-size: 14px; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self._send_button.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_button)

        layout.addLayout(input_layout)

    def _on_send(self):
        text = self._input_field.text().strip()
        if text:
            self.append_message("user", text)
            self._input_field.clear()
            self.message_sent.emit(text)

    def append_message(self, role: str, content: str):
        if role == "user":
            html = (
                '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                '<td width="20%"></td>'
                '<td align="right">'
                f'<div style="display:inline-block; background-color:#95EC69; '
                f'padding:8px 12px; border-radius:8px; margin:4px 0; '
                f'text-align:left; font-size:14px; max-width:280px;">'
                f'{_escape_html(content)}</div>'
                '</td></tr></table>'
            )
        elif role == "system":
            html = (
                f'<div style="text-align:center; margin:6px 0;">'
                f'<span style="color:#999; font-size:11px; background:#e8e8e8; '
                f'padding:2px 8px; border-radius:4px;">'
                f'{_escape_html(content).replace(chr(10), "<br>")}</span></div>'
            )
        else:
            formatted = _format_markdown(content)
            html = (
                '<table width="100%" cellpadding="0" cellspacing="0"><tr>'
                '<td align="left">'
                f'<div style="display:inline-block; background-color:#FFFFFF; '
                f'padding:8px 12px; border-radius:8px; margin:4px 0; '
                f'border:1px solid #e0e0e0; font-size:14px; max-width:320px; '
                f'line-height:1.5;">'
                f'{formatted}</div>'
                '</td>'
                '<td width="20%"></td>'
                '</tr></table>'
            )
        self._chat_display.append(html)
        sb = self._chat_display.verticalScrollBar()
        sb.setValue(sb.maximum())

    def handle_stream_event(self, event: dict):
        etype = event.get("event_type", "")
        content = event.get("content", "")
        metadata = event.get("metadata", {})

        if self._stream_start_pos < 0:
            self._stream_start_pos = len(self._chat_display.toPlainText())

        if etype == "status":
            self._status_label.setText(content)

        elif etype == "thinking":
            if not self._current_thinking:
                self._chat_display.append(
                    '<div style="margin:4px 0; padding:6px; background-color:#f0f0f0; '
                    'border-radius:6px; color:#666; font-size:12px;">'
                    '🧠 思考中...</div>'
                )
                self._current_thinking = True
            self._status_label.setText("思考中...")

        elif etype == "tool_use":
            self._current_thinking = False
            input_str = ""
            inp = metadata.get("input", {})
            if inp:
                params = ", ".join(f'{k}="{v}"' for k, v in inp.items())
                input_str = f"<br>  参数: {params}"
            self._chat_display.append(
                f'<div style="margin:2px 0; color:#2196F3; font-size:11px; '
                f'padding:2px 8px; background:#f0f7ff; border-radius:4px;">'
                f'🔧 {content}{input_str}</div>'
            )
            self._status_label.setText(f"调用工具: {content}...")

        elif etype == "tool_result":
            display = content[:80] + "..." if len(content) > 80 else content
            self._chat_display.append(
                f'<div style="margin:2px 0; color:#4CAF50; font-size:11px; '
                f'padding:2px 8px;">✓ {_escape_html(display)}</div>'
            )

        elif etype == "text":
            if self._current_thinking:
                self._current_thinking = False
            self._text_buffer.append(content)
            self._status_label.setText("生成回复...")

        elif etype == "done":
            self._finalize_stream()

    def _finalize_stream(self):
        cursor = self._chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)

        if self._stream_start_pos >= 0:
            full_text = self._chat_display.toPlainText()
            cursor.setPosition(self._stream_start_pos)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()

        final_text = "".join(self._text_buffer)
        if final_text:
            self.append_message("assistant", final_text)

        self._status_label.setText("")
        self._reset_stream_state()

    def clear_chat(self):
        self._chat_display.clear()
        self._status_label.setText("")
        self._reset_stream_state()

    def set_input_enabled(self, enabled: bool):
        self._input_field.setEnabled(enabled)
        self._send_button.setEnabled(enabled)
