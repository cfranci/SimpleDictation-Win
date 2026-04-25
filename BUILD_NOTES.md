# SimpleDictation-Win Build Notes

## Current Issue: ModuleNotFoundError when running built .exe

When running the built `.exe` from `dist/SimpleDictation.exe`:
```
ModuleNotFoundError: No module named 'tray_controller'
```

**Root Cause:**
- Running `py main.py` from source works fine
- The built .exe doesn't include local project modules (tray_controller.py, app.py, overlay_window.py, etc.)
- PyInstaller doesn't automatically discover local .py files in the project directory

**What works:**
- Running from source: `C:\Users\lucyg\AppData\Local\Programs\Python\Launcher\py.exe main.py`
- The app works correctly when run this way

## Project Structure
```
SimpleDictation-Win/
├── main.py              # Entry point
├── app.py               # Main application
├── tray_controller.py   # System tray (NOT FOUND IN EXE)
├── overlay_window.py    # Floating mic widget (NOT FOUND IN EXE)
├── audio_recorder.py    # Audio recording
├── whisper_engine.py    # Whisper transcription
├── hotkey_listener.py   # Global hotkey detection
├── text_injector.py     # Text pasting
├── clipboard_manager.py # Clipboard handling
├── config.py            # Settings
├── requirements.txt     # Dependencies
├── icon.ico             # App icon
└── SimpleDictation.spec # PyInstaller spec file
```

## Build Attempts

1. Basic PyInstaller command - failed
2. Added --hidden-import flags - failed  
3. Used collect_all() from PyInstaller hooks - failed
4. Added datas with (current_dir, '.') - failed
5. Explicit list of local modules in hiddenimports - failed

## Attempted Spec File Solutions

```python
# Tried adding local modules explicitly
local_modules = [
    'tray_controller',
    'overlay_window', 
    'audio_recorder',
    'whisper_engine',
    'hotkey_listener',
    'text_injector',
    'clipboard_manager',
    'config',
    'app',
]
hiddenimports += local_modules
```

Also tried:
```python
# Include project directory in datas
datas += [(current_dir, '.')]
```

## PyInstaller Version
- PyInstaller 6.20.0
- Python 3.12.10
- Windows 11

## Possible Solutions to Try

1. **Use --add-binary or --add-data** to include the .py files explicitly
2. **Use a virtual environment** and build with all dependencies
3. **Try py2exe** instead of PyInstaller
4. **Use cx_Freeze** as alternative
5. **Bundle as folder** (not onefile) and include .py files
6. **Use PYTHONPATH** at runtime via environment variable in spec file

## For Claude Code

The user wants this fixed so they can run the app from a desktop shortcut without needing to open a terminal. The Python script works - just need to get PyInstaller to properly bundle the local modules.