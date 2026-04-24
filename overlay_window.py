"""Floating microphone overlay window.

A small always-on-top pill button that shows recording state,
audio level ring, and engine label. Equivalent to the macOS
FloatingMicWindow. Uses PySide6 for the overlay.
"""

import logging
import math
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QTimer, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent

logger = logging.getLogger("SimpleDictation.overlay")

PILL_WIDTH = 44
PILL_HEIGHT = 58


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

        # Position top-right of primary screen
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - PILL_WIDTH - 12, geo.top() + 40)

        # Audio level refresh timer
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

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Circle area (top 44x44)
        cx, cy = PILL_WIDTH / 2, PILL_HEIGHT - 44 + 22
        radius = 18

        # Glow ring when recording
        if self.is_recording:
            level = min(max(self.audio_level, 0), 1.0)
            ring_width = 2.0 + 3.0 * level
            ring_color = QColor(255, 50, 50, int(100 + 155 * level))
            pen = QPen(ring_color, ring_width)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(QPoint(int(cx), int(cy)), int(radius + ring_width), int(radius + ring_width))

        # Main circle
        if self.is_recording:
            p.setBrush(QBrush(QColor(220, 40, 40)))
        else:
            p.setBrush(QBrush(QColor(40, 40, 40, 65)))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPoint(int(cx), int(cy)), radius, radius)

        # Mic icon
        if self.is_recording:
            mic_color = QColor(255, 255, 255)
        else:
            mic_color = QColor(190, 190, 190, 65)

        p.setBrush(QBrush(mic_color))
        p.setPen(Qt.PenStyle.NoPen)
        # Mic body
        p.drawRoundedRect(int(cx - 4), int(cy - 1), 8, 14, 4, 4)

        # Mic arc
        pen = QPen(mic_color, 1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        arc_rect = QRect(int(cx - 7), int(cy), 14, 14)
        p.drawArc(arc_rect, 200 * 16, 140 * 16)

        # Stand
        p.drawLine(int(cx), int(cy + 14), int(cx), int(cy + 17))
        # Base
        p.drawLine(int(cx - 5), int(cy + 17), int(cx + 5), int(cy + 17))

        # Engine label
        label_color = QColor(220, 220, 220, 255 if self.is_recording else 65)
        p.setPen(label_color)
        p.setFont(QFont("Segoe UI", 7, QFont.Weight.Medium))
        p.drawText(QRect(0, PILL_HEIGHT - 14, PILL_WIDTH, 14), Qt.AlignmentFlag.AlignCenter, self.engine_label)

        p.end()

    # ------------------------------------------------------------------
    # Mouse handling
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent):
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
