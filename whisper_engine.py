"""Faster-whisper STT engine wrapper.

Manages model loading and transcription for all Whisper model sizes.
Models are downloaded on first use and cached locally.
"""

import logging
import threading
import time
import numpy as np

logger = logging.getLogger("SimpleDictation.whisper")

# Model variants matching the macOS app
MODELS = {
    "faster-whisper-tiny": {"size": "tiny", "label": "Whisper Tiny (~40MB)"},
    "faster-whisper-base": {"size": "base", "label": "Whisper Base (~140MB)"},
    "faster-whisper-small": {"size": "small", "label": "Whisper Small (~460MB)"},
    "faster-whisper-medium": {"size": "medium", "label": "Whisper Medium (~1.5GB)"},
    "faster-whisper-large-v3": {"size": "large-v3", "label": "Distil-Whisper Large v3 (~594MB)"},
}

# Known silence hallucinations (same list as macOS)
SILENCE_HALLUCINATIONS = {
    "thank you", "thanks", "thanks.", "thank you.", "thanks for watching",
    "thank you for watching", "bye", "bye.", "you", "you.", ".",
}


class WhisperEngine:
    def __init__(self):
        self._model = None
        self._loaded_size: str | None = None
        self._loading = False
        self._lock = threading.Lock()
        self.on_model_loading: callable | None = None  # (is_loading, model_name, success)

    def is_model_loaded(self, engine_key: str) -> bool:
        info = MODELS.get(engine_key)
        if not info:
            return False
        return self._loaded_size == info["size"]

    def load_model(self, engine_key: str) -> bool:
        """Load a Whisper model. Returns True on success."""
        info = MODELS.get(engine_key)
        if not info:
            logger.error("Unknown engine key: %s", engine_key)
            return False

        size = info["size"]
        if self._loaded_size == size and self._model is not None:
            return True

        with self._lock:
            if self._loading:
                return False
            self._loading = True

        if self.on_model_loading:
            self.on_model_loading(True, info["label"], False)

        try:
            from faster_whisper import WhisperModel
            logger.info("Loading faster-whisper model: %s", size)
            start = time.time()

            # Use int8 quantization for speed on CPU; use cuda if available
            try:
                self._model = WhisperModel(size, device="cuda", compute_type="float16")
                logger.info("Using CUDA GPU")
            except Exception:
                self._model = WhisperModel(size, device="cpu", compute_type="int8")
                logger.info("Using CPU with int8")

            elapsed = time.time() - start
            self._loaded_size = size
            logger.info("Model loaded in %.1fs", elapsed)

            if self.on_model_loading:
                self.on_model_loading(False, info["label"], True)
            return True

        except Exception:
            logger.exception("Failed to load model %s", size)
            if self.on_model_loading:
                self.on_model_loading(False, info["label"], False)
            return False
        finally:
            with self._lock:
                self._loading = False

    def transcribe(self, samples: np.ndarray, language: str = "en") -> str:
        """Transcribe float32 audio samples. Returns text or empty string."""
        if self._model is None:
            logger.warning("No model loaded")
            return ""

        if len(samples) < 8000:  # < 0.5s
            logger.info("Audio too short (%d samples), skipping", len(samples))
            return ""

        try:
            start = time.time()
            segments, info = self._model.transcribe(
                samples,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
            )
            text = " ".join(seg.text.strip() for seg in segments).strip()
            elapsed = time.time() - start

            # Filter hallucinations
            if text.lower() in SILENCE_HALLUCINATIONS:
                logger.info("Suppressed silence hallucination: '%s'", text)
                return ""

            logger.info("Transcribed in %.1fs: %s", elapsed, text[:80])
            return text

        except Exception:
            logger.exception("Transcription failed")
            return ""
