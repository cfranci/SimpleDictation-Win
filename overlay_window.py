"""Floating microphone overlay window."""

import logging
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent

logger = logging.getLogger("SimpleDictation.overlay")

CIRCLE_SIZE = 52
PILL_WIDTH = 120
PILL_HEIGHT = 76
BOTTOM_MARGIN = 100


class FloatingMicOverlay(QWidget):
    def __init__(self, on_toggle, on_enter, on_right_click):
        super().__init__()
        self.on_toggle = on_toggle
        self.on_enter = on_enter
        self.on_right_click_cb = on_right_click

        self.is_recording = False
        self.audio_level = 0.0
        self.engine_label = "W-B"

        self._last_click_time = 0
        self._drag_start: QPoint | None = None
        self._window_start: QPoint | None = None
        self._did_drag = False

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(PILL_WIDTH, PILL_HEIGHT)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - PILL_WIDTH) // 2
            y = geo.bottom() - PILL_HEIGHT - BOTTOM_MARGIN
            self.move(x, y)

        self._level_timer = QTimer(self)
        self._level_timer.timeout.connect(self.update)
        self._level_timer.setInterval(50)

    def set_recording(self, recording: bool):
        self.is_recording = recording
        if recording:
            self._level_timer.start()
        else:
            self._level_timer.stop()
            self.audio_level = 0.0
        self.update()

    def set_engine_label(self, label: str):
        self.engine_label = label
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg_color = QColor(35, 35, 35, 230)
        p.setBrush(QBrush(bg_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, PILL_WIDTH, PILL_HEIGHT, 10, 10)

        cx = PILL_WIDTH // 2
        cy = CIRCLE_SIZE // 2 + 8
        radius = CIRCLE_SIZE // 2 - 2

        if self.is_recording:
            level = min(max(self.audio_level, 0), 1.0)
            ring_width = 2.0 + 4.0 * level
            ring_color = QColor(255, 50, 50, int(100 + 155 * level))
            pen = QPen(ring_color, ring_width)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(cx, cy), int(radius + ring_width), int(radius + ring_width))

            p.setBrush(QBrush(QColor(220, 40, 40)))
        else:
            p.setBrush(QBrush(QColor(45, 45, 45, 200)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(cx, cy), radius, radius)

        if self.is_recording:
            mic_color = QColor(255, 255, 255)
        else:
            mic_color = QColor(200, 200, 200)

        body_width, body_height = 14, 22
        body_x = cx - body_width // 2
        body_y = cy - body_height // 2 + 2
        p.setBrush(QBrush(mic_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(int(body_x), int(body_y), body_width, body_height, 3, 3)

        arc_size = 16
        arc_x = cx - arc_size // 2
        arc_y = cy - body_height // 2 - 4
        pen = QPen(mic_color, 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRect(int(arc_x), int(arc_y), arc_size, arc_size)
        p.drawArc(arc_rect, 200 * 16, 140 * 16)

        p.drawLine(int(cx), int(body_y + body_height), int(cx), int(body_y + body_height + 3))
        p.drawLine(int(cx - 4), int(body_y + body_height + 3), int(cx + 4), int(body_y + body_height + 3))

        mid_y = int(PILL_HEIGHT // 2)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(180, 180, 180)))
        p.drawEllipse(QPoint(14, mid_y), 9, 9)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawLine(10, mid_y, 18, mid_y)

        p.setBrush(QBrush(QColor(220, 40, 40)))
        p.drawEllipse(QPoint(PILL_WIDTH - 14, mid_y), 9, 9)
        p.setPen(QPen(QColor(255, 255, 255), 1.5))
        p.drawLine(PILL_WIDTH - 17, mid_y - 3, PILL_WIDTH - 11, mid_y + 3)
        p.drawLine(PILL_WIDTH - 17, mid_y + 3, PILL_WIDTH - 11, mid_y - 3)

        label_color = QColor(220, 220, 220, 100)
        p.setPen(label_color)
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Normal))
        p.drawText(QRect(26, PILL_HEIGHT - 14, PILL_WIDTH - 52, 14), Qt.AlignmentFlag.AlignCenter, self.engine_label)

        p.end()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        mid_y = int(PILL_HEIGHT // 2)

        if abs(pos.x() - 14) < 12 and abs(pos.y() - mid_y) < 12:
            self.hide()
            return
        if abs(pos.x() - (PILL_WIDTH - 14)) < 12 and abs(pos.y() - mid_y) < 12:
            self.hide()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self._window_start = self.pos()
            self._did_drag = False
        elif event.button() == Qt.MouseButton.RightButton:
            if self.on_right_click_cb:
                self.on_right_click_cb()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_start is not None:
            delta = event.globalPosition().toPoint() - self._drag_start
            if abs(delta.x()) > 3 or abs(delta.y()) > 3:
                self._did_drag = True
            if self._did_drag and self._window_start is not None:
                self.move(self._window_start + delta)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = None
            if not self._did_drag:
                self._handle_click()

    def _handle_click(self):
        import time
        now = time.time()
        if now - self._last_click_time < 0.4:
            self._last_click_time = 0
            if self.on_enter:
                self.on_enter()
        else:
            self._last_click_time = now
            if self.on_toggle:
                self.on_toggle()