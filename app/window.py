from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from app.balance_state import is_low_balance
from app.account_dialog import AccountDialog
from app.accounts import account_display_name, load_accounts
from app.cache import load_balance_cache, save_balance_cache
from app.config import (
    get_always_on_top,
    get_refresh_interval_seconds,
    load_provider_config,
    save_provider_config,
)
from app.models import BalanceSummary
from app.panda_widget import PandaMascotWidget
from app.providers.base import BalanceProvider, ProviderError
from app.providers.factory import build_provider
from app.settings_dialog import SettingsDialog
from app.usage_chart import UsageBarChart
from app.usage_history import (
    MetricName,
    PeriodName,
    aggregate_usage,
    record_usage_snapshot,
)


def fmt_money(value: float | None, currency: str | None = None) -> str:
    if value is None:
        return "\u6682\u65e0"
    prefix = "$" if currency == "USD" else f"{currency} " if currency else ""
    return f"{prefix}{value:,.4f}" if value < 1 else f"{prefix}{value:,.2f}"


def fmt_time(value: datetime | None) -> str:
    if not value:
        return "\u6682\u65e0"
    if value.tzinfo is not None:
        value = value.astimezone()
    return value.strftime("%Y-%m-%d %H:%M:%S")


class MetricCard(QFrame):
    def __init__(
        self,
        label: str,
        parent: QWidget | None = None,
        prominent: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("PrimaryMetricCard" if prominent else "MetricCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.label = QLabel(label)
        self.label.setObjectName("Muted")
        self.value = QLabel("\u6682\u65e0")
        self.value.setObjectName("PrimaryValue" if prominent else "Value")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)
        layout.addWidget(self.label)
        layout.addWidget(self.value)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


class FloatingUsageWindow(QWidget):
    def __init__(
        self,
        provider: BalanceProvider,
        refresh_interval_seconds: int = 300,
    ) -> None:
        super().__init__()
        self.provider = provider
        self.refresh_interval_seconds = refresh_interval_seconds
        self.drag_position: QPoint | None = None
        self.details_visible = False
        self.last_summary: BalanceSummary | None = None
        self.background_colors = ("#101418", "#172033", "#1f2922", "#2a2028")
        self.background_color_index = 0
        self.always_on_top = get_always_on_top(load_provider_config())
        self.usage_metric: MetricName = "cost"
        self.usage_period: PeriodName = "week"

        self.setObjectName("Root")
        self.setWindowTitle("API \u4f59\u989d")
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(456)

        self._build_ui()
        self._load_styles()

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_balance)
        self.refresh_timer.start(self.refresh_interval_seconds * 1000)

        self._sync_provider_combo()

        cached = load_balance_cache(self.provider.provider_name)
        if cached:
            self.render_balance(cached)
            self.status_label.setText("\u7f13\u5b58")
        self.refresh_balance()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.mascot_container = QWidget()
        mascot_row = QHBoxLayout(self.mascot_container)
        mascot_row.setContentsMargins(0, 0, 0, 0)
        mascot_row.addStretch()
        self.panda = PandaMascotWidget()
        self.panda.clicked.connect(self.toggle_details)
        self.panda.drag_started.connect(self.start_drag_from_global_position)
        self.panda.dragged.connect(self.drag_to_global_position)
        self.panda.drag_finished.connect(self.finish_drag)
        mascot_row.addWidget(self.panda)
        mascot_row.addStretch()
        root.addWidget(self.mascot_container)

        self.details_panel = QFrame()
        self.details_panel.setObjectName("BalanceDetails")
        details_layout = QVBoxLayout(self.details_panel)
        details_layout.setContentsMargins(12, 12, 12, 12)
        details_layout.setSpacing(10)

        header = QHBoxLayout()
        self.title = QLabel("API \u4f59\u989d")
        self.title.setObjectName("Title")
        self.status_label = QLabel("\u5c31\u7eea")
        self.status_label.setObjectName("Muted")
        self.settings_button = QPushButton("\u8bbe\u7f6e")
        self.settings_button.clicked.connect(self.open_settings)
        self.account_button = QPushButton("\u8d26\u6237")
        self.account_button.clicked.connect(self.open_accounts)
        self.refresh_button = QPushButton("\u5237\u65b0")
        self.refresh_button.clicked.connect(self.refresh_balance)
        self.background_button = QPushButton("\u6362\u8272")
        self.background_button.setFixedWidth(44)
        self.background_button.clicked.connect(self.cycle_background_color)
        self.collapse_button = QPushButton("\u6536\u8d77")
        self.collapse_button.setFixedWidth(44)
        self.collapse_button.clicked.connect(self.toggle_details)
        self.close_button = QPushButton("\u5173\u95ed")
        self.close_button.setFixedWidth(44)
        self.close_button.clicked.connect(self.close)

        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.status_label)
        header.addWidget(self.account_button)
        header.addWidget(self.settings_button)
        header.addWidget(self.refresh_button)
        header.addWidget(self.background_button)
        header.addWidget(self.collapse_button)
        header.addWidget(self.close_button)
        details_layout.addLayout(header)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("\u5e73\u53f0"))
        self.provider_combo = QComboBox()
        self.provider_combo.currentIndexChanged.connect(self.change_provider)
        provider_row.addWidget(self.provider_combo)
        details_layout.addLayout(provider_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

        self.balance_card = MetricCard("\u4f59\u989d", prominent=True)
        self.currency_card = MetricCard("\u5e01\u79cd")
        self.available_card = MetricCard("\u53ef\u7528\u72b6\u6001")
        self.updated_card = MetricCard("\u66f4\u65b0\u65f6\u95f4")

        grid.addWidget(self.balance_card, 0, 0, 1, 2)
        grid.addWidget(self.currency_card, 1, 0)
        grid.addWidget(self.available_card, 1, 1)
        grid.addWidget(self.updated_card, 2, 0, 1, 2)
        details_layout.addLayout(grid)

        chart_header = QHBoxLayout()
        chart_header.setSpacing(6)
        self.cost_button = self._chart_button("消费")
        self.token_button = self._chart_button("Token")
        self.hour_button = self._chart_button("时")
        self.day_button = self._chart_button("日")
        self.week_button = self._chart_button("7日")
        self.month_button = self._chart_button("月")

        self.metric_group = QButtonGroup(self)
        self.metric_group.setExclusive(True)
        self.metric_group.addButton(self.cost_button)
        self.metric_group.addButton(self.token_button)
        self.cost_button.setChecked(True)

        self.period_group = QButtonGroup(self)
        self.period_group.setExclusive(True)
        self.period_group.addButton(self.hour_button)
        self.period_group.addButton(self.day_button)
        self.period_group.addButton(self.week_button)
        self.period_group.addButton(self.month_button)
        self.week_button.setChecked(True)

        self.cost_button.clicked.connect(lambda: self.set_usage_metric("cost"))
        self.token_button.clicked.connect(lambda: self.set_usage_metric("token"))
        self.hour_button.clicked.connect(lambda: self.set_usage_period("hour"))
        self.day_button.clicked.connect(lambda: self.set_usage_period("day"))
        self.week_button.clicked.connect(lambda: self.set_usage_period("week"))
        self.month_button.clicked.connect(lambda: self.set_usage_period("month"))

        chart_header.addWidget(self.cost_button)
        chart_header.addWidget(self.token_button)
        chart_header.addStretch()
        chart_header.addWidget(self.hour_button)
        chart_header.addWidget(self.day_button)
        chart_header.addWidget(self.week_button)
        chart_header.addWidget(self.month_button)
        details_layout.addLayout(chart_header)

        self.usage_chart = UsageBarChart()
        details_layout.addWidget(self.usage_chart)

        self.error_label = QLabel("")
        self.error_label.setObjectName("Error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        details_layout.addWidget(self.error_label)

        self.details_panel.hide()
        root.addWidget(self.details_panel)

    def _chart_button(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setCheckable(True)
        button.setObjectName("ChartToggle")
        return button

    def _load_styles(self) -> None:
        styles_path = Path(__file__).with_name("styles.qss")
        self.setStyleSheet(styles_path.read_text(encoding="utf-8"))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self, on_saved=self.apply_settings)
        dialog.exec()

    def open_accounts(self) -> None:
        config = load_provider_config()
        dialog = AccountDialog(
            self,
            active_provider=str(config.get("active_provider", "deepseek")),
            on_saved=lambda: self.apply_settings(load_provider_config()),
        )
        dialog.exec()

    def apply_settings(self, config: dict) -> None:
        try:
            self.provider = build_provider(config)
            self.refresh_interval_seconds = get_refresh_interval_seconds(config)
            self.set_always_on_top(get_always_on_top(config))
            self.refresh_timer.setInterval(self.refresh_interval_seconds * 1000)
            self._sync_provider_combo(config)
            self.status_label.setText("\u5df2\u91cd\u8f7d")
            self.refresh_balance()
        except Exception as exc:
            self._show_error(f"\u8bbe\u7f6e\u91cd\u8f7d\u5931\u8d25\uff1a{exc}")

    def change_provider(self) -> None:
        provider_key = self.provider_combo.currentData()
        if not provider_key:
            return

        try:
            config = load_provider_config()
            config["active_provider"] = provider_key
            save_provider_config(config)
            self.apply_settings(config)
        except Exception as exc:
            self._show_error(f"\u5e73\u53f0\u5207\u6362\u5931\u8d25\uff1a{exc}")

    def toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        self.mascot_container.setVisible(not self.details_visible)
        self.details_panel.setVisible(self.details_visible)
        self.adjustSize()

    def cycle_background_color(self) -> None:
        self.background_color_index = (
            self.background_color_index + 1
        ) % len(self.background_colors)
        background_color = self.background_colors[self.background_color_index]
        self.details_panel.setStyleSheet(
            f"QFrame#BalanceDetails {{ background: {background_color}; }}"
        )

    def refresh_balance(self) -> None:
        self.refresh_button.setEnabled(False)
        self.status_label.setText("\u5237\u65b0\u4e2d")
        self.error_label.hide()

        try:
            summary = self.provider.fetch_balance()
            self.render_balance(summary)
            save_balance_cache(summary)
            record_usage_snapshot(summary)
            self.refresh_usage_chart()
            self.status_label.setText("\u5b9e\u65f6")
        except ProviderError as exc:
            self._show_error(str(exc))
        except Exception as exc:
            self._show_error(f"\u5e73\u53f0\u9519\u8bef\uff1a{exc}")
        finally:
            self.refresh_button.setEnabled(True)

    def _show_error(self, message: str) -> None:
        self.status_label.setText("\u9519\u8bef")
        self.error_label.setText(message)
        self.error_label.show()

        cached = load_balance_cache(self.provider.provider_name)
        if cached:
            self.render_balance(cached)
            self.status_label.setText("\u7f13\u5b58")
        else:
            self.status_label.setText("\u9519\u8bef")
            self.panda.set_balance_state(self.provider.provider_name, None, None)
        self.refresh_usage_chart()

    def render_balance(self, summary: BalanceSummary) -> None:
        self.last_summary = summary
        self.balance_card.set_value(fmt_money(summary.balance, summary.currency))
        self.currency_card.set_value(summary.currency or "\u6682\u65e0")
        self.available_card.set_value(self._availability_text(summary.is_available))
        self.updated_card.set_value(fmt_time(summary.updated_at))

        self.panda.set_balance_state(
            summary.provider_name,
            is_low_balance(summary),
            summary.is_available,
        )
        self.refresh_usage_chart()
        self.adjustSize()

    def set_usage_metric(self, metric: MetricName) -> None:
        self.usage_metric = metric
        self.refresh_usage_chart()

    def set_usage_period(self, period: PeriodName) -> None:
        self.usage_period = period
        self.refresh_usage_chart()

    def refresh_usage_chart(self) -> None:
        if not hasattr(self, "usage_chart"):
            return
        bars = aggregate_usage(
            self.provider.provider_name,
            self.usage_metric,
            self.usage_period,
        )
        unit = "Token" if self.usage_metric == "token" else self.last_summary.currency if self.last_summary else ""
        self.usage_chart.set_data(bars, unit or "")

    def _availability_text(self, is_available: bool | None) -> str:
        if is_available is None:
            return "\u6682\u65e0"
        return "\u53ef\u7528" if is_available else "\u4e0d\u53ef\u7528"

    def _sync_provider_combo(self, config: dict | None = None) -> None:
        if not hasattr(self, "provider_combo"):
            return

        config = config or load_provider_config()
        active_provider = config.get("active_provider", self.provider.provider_name)
        self.provider_combo.blockSignals(True)
        self.provider_combo.clear()
        for account_id, account in load_accounts().items():
            self.provider_combo.addItem(account_display_name(account_id, account), account_id)
        index = self.provider_combo.findData(active_provider)
        if index < 0:
            index = self.provider_combo.findData(self.provider.provider_name)
        self.provider_combo.setCurrentIndex(index if index >= 0 else 0)
        self.provider_combo.blockSignals(False)

    def _apply_window_flags(self) -> None:
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def set_always_on_top(self, always_on_top: bool) -> None:
        if self.always_on_top == always_on_top:
            return
        was_visible = self.isVisible()
        self.always_on_top = always_on_top
        self._apply_window_flags()
        if was_visible:
            self.show()

    def start_drag_from_global_position(self, position: QPoint) -> None:
        self.drag_position = position - self.frameGeometry().topLeft()

    def drag_to_global_position(self, position: QPoint) -> None:
        if self.drag_position is not None:
            self.move(position - self.drag_position)

    def finish_drag(self) -> None:
        self.drag_position = None

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_drag_from_global_position(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self.finish_drag()
        event.accept()
