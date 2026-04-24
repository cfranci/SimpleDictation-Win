"""System tray icon and context menu.

Provides the Windows equivalent of the macOS menu bar icon.
Uses pystray for the system tray integration and Pillow for
icon rendering.
"""

import logging
import threading
from PIL import Image, ImageDraw

logger = logging.getLogger("SimpleDictation.tray")


def _create_icon_image(recording: bool = False, enabled: bool = True) -> Image.Image:
    """Draw a 64x64 tray icon."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    if not enabled:
        # Gray circle with dash
        draw.ellipse([4, 4, 60, 60], outline=(128, 128, 128, 255), width=3)
        draw.line([20, 32, 44, 32], fill=(128, 128, 128, 255), width=3)
    elif recording:
        # Red filled circle
        draw.ellipse([4, 4, 60, 60], fill=(220, 40, 40, 255))
        # White mic shape
        draw.rounded_rectangle([26, 16, 38, 40], radius=6, fill=(255, 255, 255, 255))
        draw.arc([22, 28, 42, 48], start=200, end=340, fill=(255, 255, 255, 255), width=2)
        draw.line([32, 48, 32, 52], fill=(255, 255, 255, 255), width=2)
        draw.line([26, 52, 38, 52], fill=(255, 255, 255, 255), width=2)
    else:
        # Dark circle outline
        draw.ellipse([4, 4, 60, 60], outline=(200, 200, 200, 255), width=3)
        # Gray mic shape
        draw.rounded_rectangle([26, 16, 38, 40], radius=6, fill=(200, 200, 200, 255))
        draw.arc([22, 28, 42, 48], start=200, end=340, fill=(200, 200, 200, 255), width=2)
        draw.line([32, 48, 32, 52], fill=(200, 200, 200, 255), width=2)
        draw.line([26, 52, 38, 52], fill=(200, 200, 200, 255), width=2)

    return img


class TrayController:
    def __init__(self, app):
        self.app = app
        self._icon = None
        self._recording = False
        self._enabled = True

    def start(self):
        """Create and show the system tray icon. Blocks on the calling thread."""
        import pystray
        from pystray import MenuItem, Menu

        def build_menu():
            engines = [
                ("Whisper Tiny (~40MB)", "faster-whisper-tiny"),
                ("Whisper Base (~140MB)", "faster-whisper-base"),
                ("Whisper Small (~460MB)", "faster-whisper-small"),
                ("Whisper Medium (~1.5GB)", "faster-whisper-medium"),
                ("Distil-Whisper Large v3 (~594MB)", "faster-whisper-large-v3"),
            ]
            hotkeys = [
                ("Left Ctrl", "ctrl_l"),
                ("Right Ctrl", "ctrl_r"),
                ("Left Alt", "alt_l"),
                ("Right Alt", "alt_r"),
                ("Caps Lock", "caps_lock"),
                ("Scroll Lock", "scroll_lock"),
            ]
            languages = [
                ("English", "en"), ("Spanish", "es"), ("French", "fr"),
                ("German", "de"), ("Italian", "it"), ("Portuguese", "pt"),
                ("Chinese", "zh"), ("Japanese", "ja"), ("Korean", "ko"),
                ("Hindi", "hi"), ("Arabic", "ar"), ("Russian", "ru"),
            ]

            engine_items = []
            for label, key in engines:
                engine_items.append(MenuItem(
                    label,
                    lambda _, k=key: self.app.set_engine(k),
                    checked=lambda item, k=key: self.app.current_engine == k,
                ))

            hotkey_items = []
            for label, key in hotkeys:
                hotkey_items.append(MenuItem(
                    label,
                    lambda _, k=key: self.app.set_hotkey(k),
                    checked=lambda item, k=key: self.app.current_hotkey == k,
                ))

            lang_items = []
            for label, code in languages:
                lang_items.append(MenuItem(
                    label,
                    lambda _, c=code: self.app.set_language(c),
                    checked=lambda item, c=code: self.app.current_language == c,
                ))

            return Menu(
                MenuItem("Simple Dictation", None, enabled=False),
                Menu.SEPARATOR,
                MenuItem(
                    "Status: Recording" if self._recording else "Status: Ready",
                    None,
                    enabled=False,
                ),
                Menu.SEPARATOR,
                MenuItem("Engine", Menu(*engine_items)),
                MenuItem("Hotkey", Menu(*hotkey_items)),
                MenuItem("Language", Menu(*lang_items)),
                Menu.SEPARATOR,
                MenuItem(
                    "Incremental Mode",
                    lambda _: self.app.toggle_incremental(),
                    checked=lambda item: self.app.incremental_mode,
                ),
                MenuItem(
                    "Clipboard Cycling",
                    lambda _: self.app.toggle_clipboard_cycling(),
                    checked=lambda item: self.app.clipboard_cycling,
                ),
                Menu.SEPARATOR,
                MenuItem(
                    "Turn Off" if self._enabled else "Turn On",
                    lambda _: self.app.toggle_enabled(),
                ),
                Menu.SEPARATOR,
                MenuItem("Quit", lambda _: self.app.quit()),
            )

        self._icon = pystray.Icon(
            "SimpleDictation",
            icon=_create_icon_image(recording=False),
            title="Simple Dictation",
            menu=build_menu(),
        )
        self._icon.run()

    def update_icon(self, recording: bool = False, enabled: bool = True):
        self._recording = recording
        self._enabled = enabled
        if self._icon:
            self._icon.icon = _create_icon_image(recording=recording, enabled=enabled)
            self._icon.update_menu()

    def notify(self, title: str, message: str):
        if self._icon:
            try:
                self._icon.notify(message, title)
            except Exception:
                logger.exception("Notification failed")

    def stop(self):
        if self._icon:
            self._icon.stop()
