# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for XCDE Save Editor.

Build:
    pyinstaller build/xcde_editor.spec
"""

import sys

block_cipher = None

a = Analysis(
    ['../src/xcde_editor/__main__.py'],
    pathex=['../src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'xcde_editor',
        'xcde_editor.core',
        'xcde_editor.backup',
        'xcde_editor.ui',
        'xcde_editor.ui.widgets',
        'xcde_editor.ui.dialogs',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
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
    name='xcde-save-editor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # no terminal window on Windows/macOS
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-only: request admin manifest only if needed
    # uac_admin=False,
)

# macOS: wrap in .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='XCDE Save Editor.app',
        icon=None,
        bundle_identifier='com.xcde-editor.save-editor',
        info_plist={
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
        },
    )
