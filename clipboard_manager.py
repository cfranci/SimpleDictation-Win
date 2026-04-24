"""Clipboard history tracking and Ctrl+V cycling.

Monitors the system clipboard for changes and maintains a history
of the last 10 copied items. Supports cycling through history
by pressing Ctrl+V repeatedly while holding Ctrl.
"""

import logging
import threading
import time
import pyperclip
from pynput.keyboard import Key, Controller

logger = logging.getLogger("SimpleDictation.clipboard")

_kb = Controller()
MAX_HISTORY = 10


class ClipboardManager:
    def __init__(self):
        self.history: list[str] = []
        self.enabled = True
        self._last_content = ""
        self._monitor_thread: threading.Thread | None = None
        self._running = False
        self._lock = threading.Lock()

        # Initialize with current clipboard content
        try:
            current = pyperclip.paste()
            if current and current.strip():
                self.history.append(current.strip())
                self._last_content = current
        except Exception:
            pass

    def start_monitoring(self):
        """Start background thread to watch clipboard changes."""
        if self._running:
            return
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self):
        self._running = False

    def add_to_history(self, text: str):
        """Manually add text to history (e.g., after dictation paste)."""
        if not text or not text.strip():
            return
        trimmed = text.strip()
        with self._lock:
            if self.history and self.history[0] == trimmed:
                return
            if trimmed in self.history:
                self.history.remove(trimmed)
            self.history.insert(0, trimmed)
            if len(self.history) > MAX_HISTORY:
                self.history = self.history[:MAX_HISTORY]

    def get_history(self) -> list[str]:
        with self._lock:
            return list(self.history)

    def _monitor_loop(self):
        while self._running:
            try:
                current = pyperclip.paste()
                if current and current != self._last_content:
                    self._last_content = current
                    self.add_to_history(current)
            except Exception:
                pass
            time.sleep(1.0)
