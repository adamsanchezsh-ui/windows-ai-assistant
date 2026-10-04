# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for CYPHERpc one-file Windows exe

import sys
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)

a = Analysis(
    ['src/main.py'],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'config'), 'config'),
        (str(root / '.env.example'), '.'),
        (str(root / 'START_HERE.md'), '.'),
    ],
    hiddenimports=[
        'openai',
        'anthropic',
        'httpx',
        'pydantic',
        'pydantic_settings',
        'dotenv',
        'yaml',
        'loguru',
        'customtkinter',
        'PIL',
        'pyautogui',
        'psutil',
        'edge_tts',
        'pygame',
        'mss',
        'pyperclip',
        'src',
        'src.agent',
        'src.model',
        'src.settings',
        'src.voice',
        'src.voice_cli',
        'src.desktop',
        'src.screen',
        'src.overlay',
        'src.work',
        'src.work.cli',
        'src.work.bootstrap',
        'src.core',
        'src.core.user_settings',
        'src.core.memory',
        'src.tools',
        'src.ui',
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
    name='CYPHERpc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI window; change to False for pure GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
