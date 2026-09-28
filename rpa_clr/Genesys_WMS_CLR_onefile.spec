# -*- mode: python ; coding: utf-8 -*-
# Build ONEFILE: um unico HawkTech_WMS_CLR.exe com tudo dentro (dist\HawkTech_WMS_CLR.exe).
# Para o build em pasta (onedir), use Genesys_WMS_CLR.spec.


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
    a.binaries,
    a.datas,
    [],
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
