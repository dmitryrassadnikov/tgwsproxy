# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

import customtkinter

ctk_path = os.path.dirname(customtkinter.__file__)
root_dir = os.path.abspath(os.path.join(os.path.dirname(SPEC), os.pardir))
icon_path = os.path.join(root_dir, "build", "macos", "TgWsProxy.icns")
bundle_icon = icon_path if os.path.exists(icon_path) else None

a = Analysis(
    [os.path.join(root_dir, "app.py")],
    pathex=[root_dir],
    binaries=[],
    datas=[
        (ctk_path, "customtkinter"),
        (os.path.join(root_dir, "icon.ico"), "."),
    ],
    hiddenimports=[
        "pystray._darwin",
        "PIL._tkinter_finder",
        "customtkinter",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.ciphers.algorithms",
        "cryptography.hazmat.primitives.ciphers.modes",
        "cryptography.hazmat.backends.openssl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TgWsProxy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch="universal2",
    codesign_identity=None,
    entitlements_file=None,
    icon=bundle_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TgWsProxy",
)

app = BUNDLE(
    coll,
    name="TgWsProxy.app",
    icon=bundle_icon,
    bundle_identifier="org.flowseal.tgwsproxy",
    info_plist={
        "CFBundleDisplayName": "TG WS Proxy",
        "CFBundleName": "TG WS Proxy",
        "CFBundleShortVersionString": "1.0.0",
        "LSUIElement": True,
        "NSHighResolutionCapable": True,
    },
)
