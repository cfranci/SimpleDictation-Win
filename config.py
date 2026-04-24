"""Persistent user settings stored as JSON."""

import json
import os
from pathlib import Path

_CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "SimpleDictation"
_CONFIG_FILE = _CONFIG_DIR / "settings.json"

_DEFAULTS = {
    "engine": "faster-whisper-base",
    "language": "en",
    "hotkey": "ctrl_l",
    "incremental_mode": False,
    "clipboard_cycling": True,
    "floating_window_x": None,
    "floating_window_y": None,
}

_cache: dict | None = None


def _load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if _CONFIG_FILE.exists():
        try:
            _cache = {**_DEFAULTS, **json.loads(_CONFIG_FILE.read_text())}
        except Exception:
            _cache = dict(_DEFAULTS)
    else:
        _cache = dict(_DEFAULTS)
    return _cache


def get(key: str):
    return _load().get(key, _DEFAULTS.get(key))


def set(key: str, value):
    data = _load()
    data[key] = value
    _save(data)


def _save(data: dict):
    global _cache
    _cache = data
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_FILE.write_text(json.dumps(data, indent=2))
