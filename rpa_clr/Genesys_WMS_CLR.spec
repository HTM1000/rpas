# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Genesys_WMS_CLR.py'],
    pathex=[],
    binaries=[],
    datas=[('image.ico', '.'), ('imagelogo.png', '.')],
    hiddenimports=['pythoncom', 'win32com', 'win32com.client', 'win32timezone', 'supabase', 'postgrest', 'httpx', 'supabase_auth', 'realtime', 'storage3', 'PIL', 'PIL.Image', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='HawkTech_WMS_CLR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['image.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='HawkTech_WMS_CLR',
)
