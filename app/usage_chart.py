from __future__ import annotations

from math import ceil, log10

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from app.usage_history import UsageBar


class UsageBarChart(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(170)
        self.bars: list[UsageBar] = []
        self.unit = ""

    def set_data(self, bars: list[UsageBar], unit: str) -> None:
        self.bars = bars
        self.unit = unit
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#111821"))

        chart = self.rect().adjusted(36, 12, -10, -28)
        if chart.width() <= 0 or chart.height() <= 0:
            return

        max_value = max((bar.value for bar in self.bars), default=0.0)
        if max_value <= 0:
            self._draw_empty(painter)
            return

        axis_max = _nice_axis_max(max_value)
        self._draw_grid(painter, chart, axis_max)
        self._draw_bars(painter, chart, axis_max)

    def _draw_empty(self, painter: QPainter) -> None:
        painter.setPen(QColor("#8f9aa3"))
        painter.setFont(QFont("", 10))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "暂无数据")

    def _draw_grid(self, painter: QPainter, chart: QRectF, axis_max: float) -> None:
        grid_pen = QPen(QColor("#2f3942"), 1)
        painter.setPen(grid_pen)
        painter.setFont(QFont("", 8))

        for index in range(4):
            y = chart.bottom() - chart.height() * index / 3
            painter.drawLine(chart.left(), y, chart.right(), y)
            value = axis_max * index / 3
            painter.setPen(QColor("#8f9aa3"))
            painter.drawText(0, int(y - 8), 32, 16, Qt.AlignmentFlag.AlignRight, _fmt_axis(value))
            painter.setPen(grid_pen)

        painter.setPen(QColor("#8f9aa3"))
        labels = self._visible_labels()
        if not labels:
            return
        bar_slot = chart.width() / max(len(self.bars), 1)
        for index, label in labels:
            x = chart.left() + bar_slot * index + bar_slot / 2
            painter.drawText(
                int(x - 24),
                int(chart.bottom() + 6),
                48,
                18,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

    def _draw_bars(self, painter: QPainter, chart: QRectF, axis_max: float) -> None:
        if not self.bars:
            return

        slot = chart.width() / len(self.bars)
        width = max(5.0, min(24.0, slot * 0.58))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#1688f0"))

        for index, bar in enumerate(self.bars):
            if bar.value <= 0:
                continue
            height = max(2.0, chart.height() * bar.value / axis_max)
            x = chart.left() + slot * index + (slot - width) / 2
            y = chart.bottom() - height
            painter.drawRoundedRect(QRectF(x, y, width, height), 4, 4)

    def _visible_labels(self) -> list[tuple[int, str]]:
        count = len(self.bars)
        if count <= 8:
            step = 1
        elif count <= 16:
            step = 2
        else:
            step = max(1, count // 6)
        return [
            (index, bar.label)
            for index, bar in enumerate(self.bars)
            if index % step == 0 or index == count - 1
        ]


def _nice_axis_max(value: float) -> float:
    if value <= 0:
        return 1.0
    magnitude = 10 ** floor_log10(value)
    normalized = value / magnitude
    if normalized <= 2:
        nice = 2
    elif normalized <= 5:
        nice = 5
    else:
        nice = 10
    return nice * magnitude


def floor_log10(value: float) -> int:
    return int(log10(value)) if value >= 1 else -ceil(abs(log10(value)))


def _fmt_axis(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    if value >= 10:
        return f"{value:.0f}"
    if value >= 1:
        return f"{value:.1f}"
    return f"{value:.2f}"
