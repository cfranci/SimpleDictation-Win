# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for SimpleDictation.

Explicitly collects all local project modules so they're bundled
into the .exe. This fixes the ModuleNotFoundError for tray_controller,
overlay_window, etc.
"""

import os
import sys

block_cipher = None
project_dir = os.path.dirname(os.path.abspath(SPEC))

# Explicitly list every local .py module so PyInstaller bundles them
local_modules = [
    'app',
    'audio_recorder',
    'clipboard_manager',
    'config',
    'hotkey_listener',
    'overlay_window',
    'text_injector',
    'tray_controller',
    'whisper_engine',
]

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
    ],
    hiddenimports=local_modules + [
        'pystray._win32',
        'PIL._tkinter_finder',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SimpleDictation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
