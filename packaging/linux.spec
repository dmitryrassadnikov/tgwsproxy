# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# customtkinter ships JSON themes + assets that must be bundled
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

a = Analysis(
    [os.path.join(os.path.dirname(SPEC), os.pardir, 'linux.py')],
    pathex=[],
    binaries=[],
    datas=[(ctk_path, 'customtkinter/')],
    hiddenimports=[
        'pystray._appindicator',
        'PIL._tkinter_finder',
        'customtkinter',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.modes',
        'cryptography.hazmat.backends.openssl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

icon_path = os.path.join(os.path.dirname(SPEC), os.pardir, 'icon.ico')
if os.path.exists(icon_path):
    a.datas += [('icon.ico', icon_path, 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TgWsProxy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
