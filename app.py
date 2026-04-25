"""SimpleDictation for Windows -- main application.

Wires together all components: hotkey listener, audio recorder,
whisper engine, text injector, clipboard manager, system tray,
and floating overlay window.
"""

import logging
import sys
import threading
import time
import numpy as np

import config
from audio_recorder import AudioRecorder
from whisper_engine import WhisperEngine, MODELS
from hotkey_listener import HotkeyListener
from text_injector import paste_text, press_enter, delete_chars
from clipboard_manager import ClipboardManager
from tray_controller import TrayController

logger = logging.getLogger("SimpleDictation")

# Engine label map (for overlay)
ENGINE_LABELS = {
    "faster-whisper-tiny": "W-T",
    "faster-whisper-base": "W-B",
    "faster-whisper-small": "W-S",
    "faster-whisper-medium": "W-M",
    "faster-whisper-large-v3": "DL3",
}


class SimpleDictationApp:
    def __init__(self):
        self.current_engine = config.get("engine")
        self.current_hotkey = config.get("hotkey")
        self.current_language = config.get("language")
        self.incremental_mode = config.get("incremental_mode")
        self.clipboard_cycling = config.get("clipboard_cycling")
        self.enabled = True

        self.recorder = AudioRecorder()
        self.whisper = WhisperEngine()
        self.hotkey = HotkeyListener()
        self.clipboard = ClipboardManager()
        self.tray = TrayController(self)
        self.overlay = None  # Created on Qt thread

        self._recording = False
        self._incremental_timer: threading.Timer | None = None
        self._incremental_pasted_chars = 0
        self._recording_start_time = 0.0
        self._qt_app = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def run(self):
        """Start the app. Blocks until quit."""
        # Setup whisper model loading notification
        self.whisper.on_model_loading = self._on_model_loading

        # Pre-load the selected model in background
        threading.Thread(
            target=self.whisper.load_model,
            args=(self.current_engine,),
            daemon=True,
        ).start()

        # Setup hotkey
        self.hotkey.hotkey_name = self.current_hotkey
        self.hotkey.on_start_recording = self._start_recording
        self.hotkey.on_stop_recording = self._stop_recording
        self.hotkey.on_double_tap = self._on_double_tap
        self.hotkey.start()

        # Start clipboard monitoring
        self.clipboard.start_monitoring()

        # Start Qt app for overlay window on a background thread
        self._start_overlay_thread()

        # Run the tray icon on the main thread (blocks)
        logger.info("SimpleDictation started (engine=%s, hotkey=%s, lang=%s)",
                     self.current_engine, self.current_hotkey, self.current_language)
        self.tray.start()

    def quit(self):
        logger.info("Quitting")
        self.hotkey.stop()
        self.clipboard.stop_monitoring()
        if self.overlay:
            try:
                self.overlay.close()
            except Exception:
                pass
        if self._qt_app:
            self._qt_app.quit()
        self.tray.stop()

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _start_recording(self):
        if not self.enabled or self._recording:
            return

        self._recording = True
        self._recording_start_time = time.time()
        self._incremental_pasted_chars = 0

        self.recorder.start()
        self.tray.update_icon(recording=True)
        if self.overlay:
            self.overlay.set_recording(True)

        # Start incremental transcription timer if enabled
        if self.incremental_mode:
            self._start_incremental_timer()

        logger.info("Recording started")

    def _stop_recording(self):
        if not self._recording:
            return

        self._recording = False
        self._stop_incremental_timer()

        samples = self.recorder.stop()
        self.tray.update_icon(recording=False)
        if self.overlay:
            self.overlay.set_recording(False)

        if samples is None or len(samples) < 8000:
            logger.info("Recording too short, skipping transcription")
            return

        # Check minimum recording duration (400ms guard, same as macOS)
        if time.time() - self._recording_start_time < 0.4:
            logger.info("Recording duration < 400ms, skipping")
            return

        # Transcribe in background thread
        threading.Thread(
            target=self._transcribe_and_paste,
            args=(samples,),
            daemon=True,
        ).start()

    def _transcribe_and_paste(self, samples: np.ndarray):
        """Final transcription after recording stops."""
        text = self.whisper.transcribe(samples, language=self.current_language)
        if not text:
            return

        if self.incremental_mode and self._incremental_pasted_chars > 0:
            # Delete old incremental text, paste final
            delete_chars(self._incremental_pasted_chars)
            time.sleep(0.03)

        paste_text(text)
        self.clipboard.add_to_history(text)
        logger.info("Final: %s", text[:80])

    def _on_double_tap(self):
        press_enter()

    # ------------------------------------------------------------------
    # Incremental transcription
    # ------------------------------------------------------------------

    def _start_incremental_timer(self):
        self._stop_incremental_timer()
        self._incremental_tick()

    def _stop_incremental_timer(self):
        if self._incremental_timer:
            self._incremental_timer.cancel()
            self._incremental_timer = None

    def _incremental_tick(self):
        if not self._recording or not self.incremental_mode:
            return

        # Schedule next tick
        self._incremental_timer = threading.Timer(5.0, self._incremental_tick)
        self._incremental_timer.daemon = True
        self._incremental_timer.start()

        # Get current samples
        with self.recorder._lock:
            if not self.recorder.samples:
                return
            samples = np.concatenate(self.recorder.samples)

        if len(samples) < 16000:  # Need at least 1s
            return

        # Transcribe
        text = self.whisper.transcribe(samples, language=self.current_language)
        if not text:
            return

        # Delete old text and paste new
        if self._incremental_pasted_chars > 0:
            delete_chars(self._incremental_pasted_chars)
            time.sleep(0.03)

        paste_text(text)
        self._incremental_pasted_chars = len(text) + 1  # +1 for trailing space

    # ------------------------------------------------------------------
    # Settings (called from tray menu)
    # ------------------------------------------------------------------

    def set_engine(self, engine_key: str):
        self.current_engine = engine_key
        config.set("engine", engine_key)

        label = ENGINE_LABELS.get(engine_key, engine_key)
        if self.overlay:
            self.overlay.set_engine_label(label)

        # Load model in background
        threading.Thread(
            target=self.whisper.load_model,
            args=(engine_key,),
            daemon=True,
        ).start()

        logger.info("Engine changed to %s", engine_key)

    def set_hotkey(self, hotkey_name: str):
        self.current_hotkey = hotkey_name
        config.set("hotkey", hotkey_name)
        self.hotkey.stop()
        self.hotkey.hotkey_name = hotkey_name
        self.hotkey.start()
        logger.info("Hotkey changed to %s", hotkey_name)

    def set_language(self, language: str):
        self.current_language = language
        config.set("language", language)
        logger.info("Language changed to %s", language)

    def toggle_incremental(self):
        self.incremental_mode = not self.incremental_mode
        config.set("incremental_mode", self.incremental_mode)
        logger.info("Incremental mode: %s", self.incremental_mode)

    def toggle_clipboard_cycling(self):
        self.clipboard_cycling = not self.clipboard_cycling
        config.set("clipboard_cycling", self.clipboard_cycling)
        logger.info("Clipboard cycling: %s", self.clipboard_cycling)

    def show_overlay(self):
        if self.overlay:
            self.overlay.show()

    def toggle_enabled(self):
        self.enabled = not self.enabled
        if not self.enabled and self._recording:
            self._stop_recording()
        self.tray.update_icon(recording=self._recording, enabled=self.enabled)
        logger.info("Enabled: %s", self.enabled)

    # ------------------------------------------------------------------
    # Overlay window (Qt thread)
    # ------------------------------------------------------------------

    def _start_overlay_thread(self):
        t = threading.Thread(target=self._run_overlay, daemon=True)
        t.start()

    def _run_overlay(self):
        from PySide6.QtWidgets import QApplication
        from overlay_window import FloatingMicOverlay

        self._qt_app = QApplication.instance() or QApplication(sys.argv)

        self.overlay = FloatingMicOverlay(
            on_toggle=lambda: (self._start_recording() if not self._recording else self._stop_recording()),
            on_enter=self._on_double_tap,
            on_right_click=lambda: None,
        )
        label = ENGINE_LABELS.get(self.current_engine, self.current_engine)
        self.overlay.set_engine_label(label)
        self.overlay.show()

        # Feed audio level from recorder to overlay
        from PySide6.QtCore import QTimer
        level_timer = QTimer()
        level_timer.timeout.connect(self._sync_audio_level)
        level_timer.start(50)

        self._qt_app.exec()

    def _sync_audio_level(self):
        if self.overlay and self._recording:
            self.overlay.audio_level = self.recorder.audio_level

    # ------------------------------------------------------------------
    # Model loading callbacks
    # ------------------------------------------------------------------

    def _on_model_loading(self, is_loading: bool, model_name: str, success: bool):
        if is_loading:
            self.tray.notify("SimpleDictation", f"Downloading {model_name}...")
        else:
            if success:
                self.tray.notify("SimpleDictation", f"{model_name} ready")
            else:
                self.tray.notify("SimpleDictation", f"{model_name} failed to load")
