"""Inject transcribed text into the focused application.

Uses clipboard + Ctrl+V for reliable Unicode support across all apps.
Falls back to character-by-character typing if clipboard paste fails.
"""

import logging
import time
import platform
import ctypes
from ctypes import wintypes

logger = logging.getLogger("SimpleDictation.injector")

# Try win32clipboard first, fall back to tkinter
def _copy_to_clipboard(text: str):
    """Copy text to clipboard using Windows API."""
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32clipboard.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        pass
    
    try:
        import tkinter as tk
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(text)
        r.update()
        r.destroy()
        return True
    except Exception:
        pass
    
    return False


def paste_text(text: str):
    """Copy text to clipboard and simulate Ctrl+V to paste it."""
    if not text:
        return

    text_with_space = text + " "

    if not _copy_to_clipboard(text_with_space):
        logger.warning("Clipboard copy failed")
        return

    time.sleep(0.05)

    try:
        VK_CONTROL = 0x11
        VK_V = 0x56
        
        keybd_event = ctypes.windll.user32.keybd_event
        keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.02)
        keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        keybd_event(VK_V, 0, 2, 0)
        time.sleep(0.02)
        keybd_event(VK_CONTROL, 0, 2, 0)

        logger.info("Pasted %d chars via Ctrl+V", len(text_with_space))
    except Exception:
        logger.exception("Paste failed")


def press_enter():
    """Simulate pressing Enter."""
    try:
        VK_RETURN = 0x0D
        keybd_event = ctypes.windll.user32.keybd_event
        keybd_event(VK_RETURN, 0, 0, 0)
        time.sleep(0.02)
        keybd_event(VK_RETURN, 0, 2, 0)
    except Exception:
        logger.exception("Enter press failed")


def delete_chars(count: int):
    """Delete characters via Backspace."""
    if count <= 0:
        return
    try:
        VK_BACK = 0x08
        keybd_event = ctypes.windll.user32.keybd_event
        for _ in range(count):
            keybd_event(VK_BACK, 0, 0, 0)
            time.sleep(0.01)
            keybd_event(VK_BACK, 0, 2, 0)
        time.sleep(0.03)
    except Exception:
        logger.exception("Backspace delete failed")
