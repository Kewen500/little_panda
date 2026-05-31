from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPoint, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget


class PandaMascotWidget(QWidget):
    clicked = Signal()
    drag_started = Signal(QPoint)
    dragged = Signal(QPoint)
    drag_finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PandaMascot")
        self.setFixedSize(230, 220)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mood = "unknown"
        self.provider_name = ""
        self.phase = 0
        self.press_position: QPoint | None = None
        self.dragging = False
        asset_path = Path(__file__).resolve().parents[1] / "assets" / "panda.png"
        self.panda_pixmap = QPixmap(str(asset_path)) if asset_path.exists() else QPixmap()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(120)

    def set_balance_state(
        self,
        provider_name: str,
        is_low_balance: bool | None,
        is_available: bool | None,
    ) -> None:
        self.provider_name = provider_name
        if is_available is False or is_low_balance is True:
            self.mood = "tired"
            self.timer.stop()
        elif is_low_balance is False:
            self.mood = "active"
            if not self.timer.isActive():
                self.timer.start(120)
        else:
            self.mood = "unknown"
            self.timer.stop()
        self.update()

    def _tick(self) -> None:
        self.phase = (self.phase + 1) % 10_000
        self.update()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.press_position = event.globalPosition().toPoint()
            self.dragging = False
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not event.buttons() & Qt.MouseButton.LeftButton or self.press_position is None:
            return

        current_position = event.globalPosition().toPoint()
        if not self.dragging:
            distance = current_position - self.press_position
            if distance.manhattanLength() < 4:
                return
            self.dragging = True
            self.drag_started.emit(self.press_position)
        self.dragged.emit(current_position)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.drag_finished.emit()
            else:
                self.clicked.emit()
            self.press_position = None
            self.dragging = False
            event.accept()

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_active = self.mood == "active"
        is_tired = self.mood == "tired"
        bounce = -abs(math.sin(self.phase / 4)) * 10 if is_active else 0
        sway = math.sin(self.phase / 5) * 8 if is_active else 0
        cx = self.width() / 2
        cy = 120 + bounce

        self._draw_shadow(painter, cx, cy, is_active)
        if self.panda_pixmap.isNull():
            self._draw_body(painter, cx, cy, sway, is_tired)
        else:
            self._draw_pixmap_panda(painter, cx, cy, is_tired)

    def _draw_shadow(self, painter: QPainter, cx: float, cy: float, is_active: bool) -> None:
        width = 88 if is_active else 104
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 70))
        painter.drawEllipse(QRectF(cx - width / 2, cy + 58, width, 14))

    def _draw_body(
        self, painter: QPainter, cx: float, cy: float, sway: float, is_tired: bool
    ) -> None:
        white = QColor("#f6f1e8" if not is_tired else "#d8d4cc")
        black = QColor("#181b20" if not is_tired else "#3a3d42")
        brown = QColor("#a96a35" if not is_tired else "#6f6258")

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(black)
        painter.drawEllipse(QRectF(cx - 64 + sway * 0.1, cy - 94, 44, 44))
        painter.drawEllipse(QRectF(cx + 20 + sway * 0.1, cy - 94, 44, 44))

        painter.setBrush(white)
        painter.drawEllipse(QRectF(cx - 68, cy - 78, 136, 110))
        painter.drawEllipse(QRectF(cx - 56, cy - 5, 112, 92))

        arm_angle = math.sin(self.phase / 3) * 25 if self.mood == "active" else -20
        self._draw_arm(painter, cx - 46, cy + 10, arm_angle, black)
        self._draw_arm(painter, cx + 46, cy + 10, -arm_angle, black)

        painter.setBrush(black)
        painter.drawEllipse(QRectF(cx - 42, cy - 48, 34, 44))
        painter.drawEllipse(QRectF(cx + 8, cy - 48, 34, 44))
        painter.drawEllipse(QRectF(cx - 44, cy + 58, 38, 30))
        painter.drawEllipse(QRectF(cx + 6, cy + 58, 38, 30))

        if is_tired:
            pen = QPen(QColor("#f6f1e8"), 4)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(int(cx - 34), int(cy - 28), int(cx - 18), int(cy - 24))
            painter.drawLine(int(cx + 18), int(cy - 24), int(cx + 34), int(cy - 28))
        else:
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - 32, cy - 38, 20, 24))
            painter.drawEllipse(QRectF(cx + 12, cy - 38, 20, 24))
            painter.setBrush(brown)
            painter.drawEllipse(QRectF(cx - 27, cy - 31, 10, 12))
            painter.drawEllipse(QRectF(cx + 17, cy - 31, 10, 12))
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(QRectF(cx - 24, cy - 30, 4, 4))
            painter.drawEllipse(QRectF(cx + 20, cy - 30, 4, 4))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#111318"))
        painter.drawEllipse(QRectF(cx - 12, cy - 14, 24, 16))

        smile_pen = QPen(QColor("#5f2c2f" if not is_tired else "#6a6160"), 3)
        smile_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(smile_pen)
        if is_tired:
            painter.drawArc(QRectF(cx - 16, cy + 10, 32, 18), 20 * 16, 140 * 16)
        else:
            painter.drawArc(QRectF(cx - 17, cy + 0, 34, 22), 200 * 16, 140 * 16)

    def _draw_pixmap_panda(
        self, painter: QPainter, cx: float, cy: float, is_tired: bool
    ) -> None:
        target = QRectF(cx - 82, cy - 92, 164, 164)
        painter.save()
        if is_tired:
            painter.setOpacity(0.55)
        painter.drawPixmap(target.toRect(), self.panda_pixmap)
        painter.restore()

    def _draw_arm(
        self, painter: QPainter, x: float, y: float, angle: float, color: QColor
    ) -> None:
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(-16, -16, 34, 70))
        painter.restore()
