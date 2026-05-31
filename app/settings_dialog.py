from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.accounts import account_display_name, load_accounts
from app.config import get_always_on_top, load_provider_config, save_provider_config


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        on_saved: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.on_saved = on_saved
        self.config = load_provider_config()

        self.setWindowTitle("设置")
        self.setFixedWidth(360)
        self._build_ui()
        self._populate_fields()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("通用设置")
        title.setObjectName("Title")
        root.addWidget(title)

        form = QFormLayout()
        form.setSpacing(8)
        self.active_provider = QComboBox()
        for account_id, account in load_accounts().items():
            self.active_provider.addItem(account_display_name(account_id, account), account_id)
        self.refresh_interval = QSpinBox()
        self.refresh_interval.setRange(1, 86_400)
        self.refresh_interval.setSuffix(" 秒")
        self.always_on_top = QCheckBox("保持在其他窗口上方")
        form.addRow("当前平台", self.active_provider)
        form.addRow("刷新间隔", self.refresh_interval)
        form.addRow("窗口置顶", self.always_on_top)
        root.addLayout(form)

        note = QLabel("URL 和 API Key 请在“账户”窗口中填写。")
        note.setObjectName("Muted")
        root.addWidget(note)

        actions = QHBoxLayout()
        actions.addStretch()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)
        root.addLayout(actions)

    def _populate_fields(self) -> None:
        index = self.active_provider.findData(
            self.config.get("active_provider", "deepseek")
        )
        self.active_provider.setCurrentIndex(index if index >= 0 else 0)
        self.refresh_interval.setValue(
            int(self.config.get("refresh_interval_seconds", 300))
        )
        self.always_on_top.setChecked(get_always_on_top(self.config))

    def save_settings(self) -> None:
        self.config["active_provider"] = self.active_provider.currentData()
        self.config["refresh_interval_seconds"] = self.refresh_interval.value()
        self.config["always_on_top"] = self.always_on_top.isChecked()
        save_provider_config(self.config)
        if self.on_saved:
            self.on_saved(self.config)
        self.accept()
