# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Terminal Emulator
Builds a standalone executable with PySide6 and React UI

Usage:
    pyinstaller terminal-emulator.spec

Output:
    dist/TerminalEmulator/ - Folder distribution (LGPL compliant)
    dist/TerminalEmulator.exe - Main executable

LGPL Compliance:
    - PySide6 DLLs are kept separate (not statically linked)
    - This allows commercial distribution while remaining LGPL compliant
    - Include LICENSE.txt in distribution
"""

block_cipher = None

# Data files to include (React build)
datas = [
    ('ui/react/dist', 'ui/react/dist'),
]

# Hidden imports
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebChannel',
    'requests',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    [],
    exclude_binaries=True,
    name='TerminalEmulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add your .ico file here if desired
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TerminalEmulator',
)

# Alternative: Single file distribution
# Uncomment below and comment out COLLECT above
# This creates a single .exe but STILL keeps PySide6 DLLs separate (LGPL compliant)

# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='TerminalEmulator',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
# )
