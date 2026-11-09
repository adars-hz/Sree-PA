# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

root_dir = Path.cwd()

datas = [
    (str(root_dir / 'frontend'), 'frontend'),
    (str(root_dir / 'scripts'), 'scripts'),
    (str(root_dir / '.env.example'), '.'),
]

hidden_imports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespans',
    'uvicorn.lifespans.on',
    'uvicorn.lifespans.off',
    'fastapi',
    'fastapi.staticfiles',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.staticfiles',
    'starlette.responses',
    'pydantic',
    'pydantic_core',
    'pyautogui',
    'numpy',
    'scipy',
    'scipy.signal',
    'scipy.io.wavfile',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'sqlite3',
    'backend.app.main',
    'backend.app.api.router',
    'backend.app.api.chat',
    'backend.app.api.voice',
    'backend.app.api.desktop',
    'backend.app.api.system',
    'backend.app.api.automation',
    'backend.app.api.memory',
    'backend.app.api.notes',
    'backend.app.api.reminders',
    'backend.app.api.search',
    'backend.app.api.data',
    'backend.app.automation.desktop_control',
    'backend.app.automation.screen_share',
    'backend.app.automation.crystallizer',
    'backend.app.automation.executor',
    'backend.app.automation.security_guard',
    'backend.app.automation.path_resolver',
    'backend.app.audio.voice_biometrics',
    'backend.app.database.db',
    'backend.app.ai.universal_router',
    'backend.app.ai.ollama_client',
]

a = Analysis(
    ['run_sree_app.py'],
    pathex=[str(root_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'tkinter', 'pandas'],
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
    name='SREE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True, # Allows users to see SREE status and server logs
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='sree.ico',
)

