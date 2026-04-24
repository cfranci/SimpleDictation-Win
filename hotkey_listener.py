"""Global hotkey listener for hold-to-talk and double-tap detection.

Monitors modifier key state globally using pynput. Supports:
- Hold-to-talk: start recording on key down, stop on key up
- Double-tap: press Enter when the key is tapped twice quickly
"""

import logging
import time
import threading
from pynput.keyboard import Key, Listener, KeyCode

logger = logging.getLogger("SimpleDictation.hotkey")

# Map config strings to pynput keys
KEY_MAP = {
    "ctrl_l": Key.ctrl_l,
    "ctrl_r": Key.ctrl_r,
    "alt_l": Key.alt_l,
    "alt_r": Key.alt_r,
    "shift_l": Key.shift_l,
    "shift_r": Key.shift_r,
    "caps_lock": Key.caps_lock,
    "f13": Key.f13,
    "f14": Key.f14,
    "scroll_lock": Key.scroll_lock,
}

DOUBLE_TAP_THRESHOLD = 0.4  # seconds


class HotkeyListener:
    def __init__(self):
        self.hotkey_name: str = "ctrl_l"
        self.on_start_recording: callable | None = None
        self.on_stop_recording: callable | None = None
        self.on_double_tap: callable | None = None
        self.enabled = True

        self._hotkey_pressed = False
        self._last_release_time = 0.0
        self._listener: Listener | None = None
        self._running = False

    @property
    def _hotkey(self):
        return KEY_MAP.get(self.hotkey_name, Key.ctrl_l)

    def start(self):
        """Start listening for the hotkey globally."""
        if self._running:
            return
        self._running = True
        self._listener = Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started (key=%s)", self.hotkey_name)

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _on_press(self, key):
        if not self.enabled:
            return
        if not self._matches_hotkey(key):
            return
        if self._hotkey_pressed:
            return  # Already held down (key repeat)

        self._hotkey_pressed = True

        # Double-tap detection: if released < 400ms ago, send Enter
        now = time.time()
        if now - self._last_release_time < DOUBLE_TAP_THRESHOLD:
            logger.info("Double-tap detected, pressing Enter")
            if self.on_double_tap:
                self.on_double_tap()
            return

        logger.info("Hotkey pressed, starting recording")
        if self.on_start_recording:
            self.on_start_recording()

    def _on_release(self, key):
        if not self.enabled:
            return
        if not self._matches_hotkey(key):
            return
        if not self._hotkey_pressed:
            return

        self._hotkey_pressed = False
        self._last_release_time = time.time()

        logger.info("Hotkey released, stopping recording")
        if self.on_stop_recording:
            self.on_stop_recording()

    def _matches_hotkey(self, key) -> bool:
        """Check if the pressed/released key matches our configured hotkey."""
        target = self._hotkey
        if key == target:
            return True
        # Some systems report Key.ctrl instead of Key.ctrl_l
        if isinstance(target, Key):
            name = target.name
            if name.endswith("_l") or name.endswith("_r"):
                base = name[:-2]
                try:
                    if key == Key[base]:
                        return True
                except (KeyError, AttributeError):
                    pass
        return False
