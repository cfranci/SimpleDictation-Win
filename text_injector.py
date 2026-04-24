"""Inject transcribed text into the focused application.

Uses clipboard + Ctrl+V for reliable Unicode support across all apps.
Falls back to character-by-character typing if clipboard paste fails.
"""

import logging
import time
import pyperclip
from pynput.keyboard import Controller, Key

logger = logging.getLogger("SimpleDictation.injector")

_kb = Controller()


def paste_text(text: str):
    """Copy text to clipboard and simulate Ctrl+V to paste it.

    Adds a trailing space after the text (matching macOS behavior)
    so the cursor is ready for the next word.
    """
    if not text:
        return

    text_with_space = text + " "

    try:
        pyperclip.copy(text_with_space)
        time.sleep(0.05)

        _kb.press(Key.ctrl)
        time.sleep(0.02)
        _kb.press("v")
        time.sleep(0.02)
        _kb.release("v")
        time.sleep(0.02)
        _kb.release(Key.ctrl)

        logger.info("Pasted %d chars via Ctrl+V", len(text_with_space))
    except Exception:
        logger.exception("Paste failed, falling back to typing")
        try:
            _kb.type(text_with_space)
        except Exception:
            logger.exception("Type fallback also failed")


def press_enter():
    """Simulate pressing Enter (for form submission / chat send)."""
    try:
        _kb.press(Key.enter)
        time.sleep(0.02)
        _kb.release(Key.enter)
    except Exception:
        logger.exception("Enter press failed")


def delete_chars(count: int):
    """Delete *count* characters via Backspace (for incremental mode)."""
    if count <= 0:
        return
    try:
        for _ in range(count):
            _kb.press(Key.backspace)
            _kb.release(Key.backspace)
        time.sleep(0.03)
    except Exception:
        logger.exception("Backspace delete failed")
