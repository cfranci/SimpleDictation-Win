"""Microphone capture with real-time audio level metering.

Records 16kHz mono float32 audio for STT engines. Provides a
callback-based interface for audio level visualization.
"""

import threading
import logging
import numpy as np

try:
    import sounddevice as sd
except OSError:
    sd = None

logger = logging.getLogger("SimpleDictation.audio")

SAMPLE_RATE = 16_000
CHANNELS = 1
BLOCK_SIZE = 1024


class AudioRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_level = 0.0
        self.samples: list[np.ndarray] = []
        self._stream = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def list_devices(self) -> list[dict]:
        """Return input devices as [{"index": int, "name": str}, ...]."""
        if sd is None:
            return []
        devices = sd.query_devices()
        result = []
        for i, d in enumerate(devices):
            if d["max_input_channels"] > 0:
                result.append({"index": i, "name": d["name"]})
        return result

    def start(self, device_index: int | None = None):
        """Start recording from *device_index* (None = default mic)."""
        if self.is_recording:
            return
        if sd is None:
            logger.error("sounddevice not available (PortAudio missing?)")
            return

        self.samples = []
        self.audio_level = 0.0
        self.is_recording = True

        try:
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype="float32",
                blocksize=BLOCK_SIZE,
                device=device_index,
                callback=self._audio_callback,
            )
            self._stream.start()
            logger.info("Recording started (device=%s)", device_index)
        except Exception:
            logger.exception("Failed to start audio stream")
            self.is_recording = False
            self._stream = None

    def stop(self) -> np.ndarray | None:
        """Stop recording and return concatenated float32 samples, or None."""
        if not self.is_recording:
            return None
        self.is_recording = False

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                logger.exception("Error stopping audio stream")
            self._stream = None

        with self._lock:
            if not self.samples:
                return None
            result = np.concatenate(self.samples)
            self.samples = []

        logger.info("Recording stopped (%d samples, %.1fs)", len(result), len(result) / SAMPLE_RATE)
        return result

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        if status:
            logger.warning("Audio callback status: %s", status)

        mono = indata[:, 0]

        # Compute RMS audio level (same formula as macOS version)
        rms = np.sqrt(np.mean(mono ** 2))
        avg_power = 20 * np.log10(max(rms, 1e-6))
        self.audio_level = max(0.0, (avg_power + 50) / 50.0)

        with self._lock:
            self.samples.append(mono.copy())
