# SimpleDictation for Windows

Hold a key, talk, release. Your words get typed wherever your cursor is. Works in any app.

## How It Works

1. Hold down **Left Ctrl** (configurable)
2. Talk into your mic
3. Release the key
4. The text gets typed out wherever your cursor is

Double-tap the key to press Enter (submits forms, sends messages).

## Quick Start

### Option A: Run from source

1. Install [Python 3.10+](https://www.python.org/downloads/)
2. Open a terminal in this folder and run:

```
pip install -r requirements.txt
python main.py
```

### Option B: Build a standalone .exe

```
build.bat
```

The .exe will be in the `dist/` folder.

## First Run

- The app appears as an icon in your **system tray** (bottom-right of your taskbar)
- A small **floating mic button** appears on screen
- The first time you select an engine, the model downloads automatically

## Choosing an Engine

Right-click the tray icon to switch engines:

| Engine | Download Size | Speed | Accuracy |
|--------|--------------|-------|----------|
| Whisper Tiny | ~40 MB | Fast | Fair |
| Whisper Base | ~140 MB | Fast | Good |
| Whisper Small | ~460 MB | Medium | Better |
| Whisper Medium | ~1.5 GB | Slower | Great |
| Distil-Whisper Large v3 | ~594 MB | Medium | Best |

**Start with Whisper Base** (the default). If you want better accuracy, try Whisper Small or Distil-Whisper Large v3.

If you have an NVIDIA GPU, models run much faster with CUDA (installed automatically with faster-whisper).

## Controls

| Action | How |
|--------|-----|
| Record | Hold **Left Ctrl** (configurable in tray menu) |
| Stop and paste | Release the key |
| Submit / press Enter | Double-tap the key |
| Toggle recording | Click the floating mic button |
| Submit via button | Double-click the floating mic button |
| Open settings | Right-click the tray icon |

## Hotkey Options

You can change the hold-to-talk key in the tray menu:

- Left Ctrl (default)
- Right Ctrl
- Left Alt
- Right Alt
- Caps Lock
- Scroll Lock

## Features

- **Hold-to-talk** dictation with automatic paste
- **5 Whisper models** from fast to high-accuracy
- **GPU acceleration** (NVIDIA CUDA, auto-detected)
- **Floating mic button** with recording glow and audio level ring
- **Clipboard history** tracking (last 10 copies)
- **Incremental mode** to see partial transcription as you speak
- **12 languages** including English, Spanish, French, Chinese, Japanese
- **Double-tap to submit** for chat boxes and forms
- **System tray** with full settings menu

## Settings

Settings are saved to `%APPDATA%\SimpleDictation\settings.json` and persist between runs.

## Troubleshooting

**"No audio" or recording doesn't work:**
- Check Windows Settings > Privacy > Microphone and make sure apps can access your mic

**Text doesn't paste into some apps:**
- Some apps running as Administrator block input from non-admin processes
- Try running SimpleDictation as Administrator (right-click > Run as administrator)

**Model download is slow:**
- Models are downloaded from Hugging Face on first use
- Whisper Base is ~140MB, should take under a minute on most connections
