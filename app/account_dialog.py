from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.accounts import (
    account_display_name,
    load_accounts,
    new_custom_account,
    save_accounts,
)


class AccountDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        active_provider: str = "deepseek",
        on_saved: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.accounts = load_accounts()
        self.on_saved = on_saved
        self.loaded_provider: str | None = None

        self.setWindowTitle("账户")
        self.setFixedWidth(520)
        self._build_ui()
        self._reload_provider_combo(active_provider)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("账户配置")
        title.setObjectName("Title")
        root.addWidget(title)

        note = QLabel("API Key 使用 Windows DPAPI 加密后保存在本机。")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        root.addWidget(note)

        selector = QHBoxLayout()
        self.provider_combo = QComboBox()
        self.provider_combo.currentIndexChanged.connect(self._switch_account)
        add_button = QPushButton("新增")
        add_button.clicked.connect(self._add_account)
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self._delete_account)
        selector.addWidget(self.provider_combo)
        selector.addWidget(add_button)
        selector.addWidget(delete_button)
        root.addLayout(selector)

        form = QFormLayout()
        form.setSpacing(8)
        self.name = QLineEdit()
        self.base_url = QLineEdit()
        self.balance_endpoint = QLineEdit()
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key.setPlaceholderText("填写 API Key 或 Bearer token，不包含 Bearer 前缀")
        self.balance_path = QLineEdit()
        self.currency_path = QLineEdit()
        self.currency_default = QLineEdit()
        self.available_path = QLineEdit()
        self.auth_header = QLineEdit()
        self.auth_prefix = QLineEdit()
        form.addRow("平台名称", self.name)
        form.addRow("URL", self.base_url)
        form.addRow("余额接口", self.balance_endpoint)
        form.addRow("API Key", self.api_key)
        form.addRow("余额字段路径", self.balance_path)
        form.addRow("币种字段路径", self.currency_path)
        form.addRow("默认币种", self.currency_default)
        form.addRow("可用状态路径", self.available_path)
        form.addRow("鉴权请求头", self.auth_header)
        form.addRow("鉴权前缀", self.auth_prefix)
        root.addLayout(form)

        help_text = QLabel(
            '自定义平台示例：响应为 {"data":{"balance":12.5,"currency":"CNY"}} 时，'
            "余额字段路径填写 data.balance，币种字段路径填写 data.currency。"
        )
        help_text.setObjectName("Muted")
        help_text.setWordWrap(True)
        root.addWidget(help_text)

        actions = QHBoxLayout()
        actions.addStretch()
        save_button = QPushButton("保存")
        save_button.clicked.connect(self._save_and_close)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        actions.addWidget(save_button)
        actions.addWidget(cancel_button)
        root.addLayout(actions)

    def _reload_provider_combo(self, selected_provider: str | None = None) -> None:
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        for account_id, account in self.accounts.items():
            self.provider_combo.addItem(account_display_name(account_id, account), account_id)
        index = self.provider_combo.findData(selected_provider)
        self.provider_combo.setCurrentIndex(index if index >= 0 else 0)
        self.provider_combo.blockSignals(False)
        self._load_selected_account()

    def _switch_account(self) -> None:
        self._store_selected_account()
        self._load_selected_account()

    def _add_account(self) -> None:
        self._store_selected_account()
        account_id, account = new_custom_account()
        self.accounts[account_id] = account
        self._reload_provider_combo(account_id)

    def _delete_account(self) -> None:
        account_id = self.provider_combo.currentData()
        if account_id in {"deepseek", "kimi"}:
            return
        self.accounts.pop(account_id, None)
        self.loaded_provider = None
        self._reload_provider_combo()

    def _store_selected_account(self) -> None:
        account_id = self.loaded_provider
        if not account_id:
            return
        account = self.accounts.setdefault(account_id, {})
        account.update(
            {
                "name": self.name.text().strip() or account_id,
                "base_url": self.base_url.text().strip(),
                "balance_endpoint": self.balance_endpoint.text().strip(),
                "api_key": self.api_key.text().strip(),
                "balance_path": self.balance_path.text().strip(),
                "currency_path": self.currency_path.text().strip(),
                "currency_default": self.currency_default.text().strip(),
                "available_path": self.available_path.text().strip(),
                "auth_header": self.auth_header.text().strip(),
                "auth_prefix": self.auth_prefix.text().strip(),
            }
        )

    def _load_selected_account(self) -> None:
        account_id = self.provider_combo.currentData()
        account = self.accounts.get(account_id, {})
        self.name.setText(account.get("name", ""))
        self.base_url.setText(account.get("base_url", ""))
        self.balance_endpoint.setText(account.get("balance_endpoint", ""))
        self.api_key.setText(account.get("api_key", ""))
        self.balance_path.setText(account.get("balance_path", ""))
        self.currency_path.setText(account.get("currency_path", ""))
        self.currency_default.setText(account.get("currency_default", ""))
        self.available_path.setText(account.get("available_path", ""))
        self.auth_header.setText(account.get("auth_header", "Authorization"))
        self.auth_prefix.setText(account.get("auth_prefix", "Bearer"))
        self.loaded_provider = account_id

    def _save_and_close(self) -> None:
        self._store_selected_account()
        save_accounts(self.accounts)
        if self.on_saved:
            self.on_saved()
        self.accept()
