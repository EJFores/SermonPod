# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SermonPod
This file defines how the application should be packaged into a standalone executable.
"""

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all yt-dlp dependencies
yt_dlp_datas = collect_data_files('yt_dlp')
yt_dlp_hiddenimports = collect_submodules('yt_dlp')

# Additional hidden imports
hiddenimports = [
    'yt_dlp',
    'tkinter',
    '_tkinter',
    'certifi',  # SSL certificates for HTTPS
    'urllib3',
    'requests',
    'mutagen',  # For audio metadata
    'pycryptodomex',  # For encrypted videos
    'websockets',  # For yt-dlp
    'brotli',  # For compressed responses
    # Local modules
    'gui',
    'gui.main_window',
    'core',
    'core.downloader',
    'utils',
    'utils.config',
    'utils.file_utils',
    'utils.validators',
] + yt_dlp_hiddenimports

# Add SSL certificates data
datas = yt_dlp_datas
try:
    import certifi
    datas += [(certifi.where(), 'certifi')]
except ImportError:
    pass

# Binary dependencies - add ffmpeg if available
binaries = []
import os
ffmpeg_path = 'ffmpeg-bin/ffmpeg'
if os.path.exists(ffmpeg_path):
    binaries.append((ffmpeg_path, '.'))

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=binaries,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SermonPod',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/SermonPod.icns' if sys.platform == 'darwin' else 'assets/SermonPod.png',
)

# macOS-specific: Create .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='SermonPod.app',
        icon='assets/SermonPod.icns',
        bundle_identifier='com.sermonpod.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
        },
    )
