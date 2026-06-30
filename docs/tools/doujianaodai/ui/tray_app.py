# ui/tray_app.py
from __future__ import annotations

from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QTabWidget, QApplication,
)
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QFont, QColor
from PyQt6.QtCore import Qt, QPoint

from ui.chat_widget import ChatWidget
from ui.overview_widget import OverviewWidget
from ui.activity_log_widget import ActivityLogWidget
from ui.settings_widget import SettingsWidget


def _create_text_icon(text: str = "🧠") -> QIcon:
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setFont(QFont("Arial", 20))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
    painter.end()
    return QIcon(pixmap)


class TrayApp:
    def __init__(self, config: dict, config_path: str, on_message_sent: callable):
        self._config = config
        self._config_path = config_path
        self._on_message_sent = on_message_sent
        self._monitor_running = False
        self._agent_connected = False

        self.tray_icon = QSystemTrayIcon(_create_text_icon())
        self.tray_icon.setToolTip("逗叽脑袋 - 桌面宠物 Agent")
        self.tray_icon.activated.connect(self._on_tray_activated)

        self._build_context_menu()
        self._build_panel()

        self.tray_icon.show()

    def _build_context_menu(self):
        menu = QMenu()
        self._monitor_action = QAction("监控: 已停止")
        self._monitor_action.setEnabled(False)
        menu.addAction(self._monitor_action)

        self._agent_action = QAction("Agent: 未连接")
        self._agent_action.setEnabled(False)
        menu.addAction(self._agent_action)

        menu.addSeparator()

        open_dir_action = QAction("打开数据目录")
        open_dir_action.triggered.connect(self._open_data_dir)
        menu.addAction(open_dir_action)

        quit_action = QAction("退出")
        quit_action.triggered.connect(QApplication.quit)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)

    def _build_panel(self):
        self.panel = QWidget()
        self.panel.setWindowTitle("逗叽脑袋")
        self.panel.setFixedSize(420, 520)
        self.panel.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
        )

        layout = QVBoxLayout(self.panel)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("QTabBar::tab { padding: 6px 12px; font-size: 13px; }")

        self.chat_widget = ChatWidget()
        self.chat_widget.message_sent.connect(self._on_message_sent)
        tabs.addTab(self.chat_widget, "💬 聊天")

        self.overview_widget = OverviewWidget()
        tabs.addTab(self.overview_widget, "📊 概览")

        self.activity_log_widget = ActivityLogWidget()
        tabs.addTab(self.activity_log_widget, "📋 日志")

        self.settings_widget = SettingsWidget(
            config=self._config,
            config_path=self._config_path,
            on_config_changed=self._on_config_changed,
        )
        tabs.addTab(self.settings_widget, "⚙️ 设置")

        layout.addWidget(tabs)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.panel.isVisible():
                self.hide_panel()
            else:
                self.show_panel()

    def show_panel(self):
        geo = self.tray_icon.geometry()
        panel_x = geo.x() + geo.width() // 2 - self.panel.width() // 2
        panel_y = geo.y() + geo.height()
        self.panel.move(QPoint(panel_x, panel_y))
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def hide_panel(self):
        self.panel.hide()

    def update_monitor_status(self, running: bool):
        self._monitor_running = running
        text = "监控: 运行中 ✓" if running else "监控: 已停止"
        self._monitor_action.setText(text)

    def update_agent_status(self, connected: bool):
        self._agent_connected = connected
        text = "Agent: 已连接 ✓" if connected else "Agent: 未连接"
        self._agent_action.setText(text)

    def _on_config_changed(self, new_config: dict):
        self._config = new_config

    def _open_data_dir(self):
        import subprocess
        import os
        data_dir = os.path.expanduser("~/.pet-memory")
        os.makedirs(data_dir, exist_ok=True)
        subprocess.Popen(["open", data_dir])
