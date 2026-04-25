"""System tray icon and context menu."""

import logging
from PIL import Image, ImageDraw

logger = logging.getLogger("SimpleDictation.tray")


def _create_icon_image(recording: bool = False, enabled: bool = True) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r = 26
    
    if not enabled:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(128, 128, 128, 255), width=3)
        draw.line([cx-12, cy, cx+12, cy], fill=(128, 128, 128, 255), width=3)
    elif recording:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(220, 40, 40, 255))
        mic_w, mic_h = 10, 16
        draw.rounded_rectangle([cx-mic_w//2, cy-mic_h//2+2, cx+mic_w//2, cy+mic_h//2+2], radius=4, fill=(255, 255, 255, 255))
        arc_box = [cx-8, cy-8, cx+8, cy+8]
        draw.arc(arc_box, 200*16, 340*16, fill=(255, 255, 255, 255), width=2)
        draw.line([cx, cy+mic_h//2+2, cx, cy+mic_h//2+5], fill=(255, 255, 255, 255), width=2)
        draw.line([cx-5, cy+mic_h//2+5, cx+5, cy+mic_h//2+5], fill=(255, 255, 255, 255), width=2)
    else:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(200, 200, 200, 255), width=3)
        mic_w, mic_h = 10, 16
        mic_color = (200, 200, 200, 255)
        draw.rounded_rectangle([cx-mic_w//2, cy-mic_h//2+2, cx+mic_w//2, cy+mic_h//2+2], radius=4, fill=mic_color)
        arc_box = [cx-8, cy-8, cx+8, cy+8]
        draw.arc(arc_box, 200*16, 340*16, fill=mic_color, width=2)
        draw.line([cx, cy+mic_h//2+2, cx, cy+mic_h//2+5], fill=mic_color, width=2)
        draw.line([cx-5, cy+mic_h//2+5, cx+5, cy+mic_h//2+5], fill=mic_color, width=2)

    return img


class TrayController:
    def __init__(self, app):
        self.app = app
        self._icon = None
        self._recording = False
        self._enabled = True

    def start(self):
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
                    checked=lambda item, c=code: self.app.current_language == code,
                ))

            return Menu(
                MenuItem("Simple Dictation", None, enabled=False),
                Menu.SEPARATOR,
                MenuItem("Status: Recording" if self._recording else "Status: Ready", None, enabled=False),
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