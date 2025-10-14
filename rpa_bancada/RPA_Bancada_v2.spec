# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['RPA_Bancada_GUI_v2.py'],
    pathex=[],
    binaries=[],
    datas=[('Tecumseh.png', '.'), ('Topo.png', '.'), ('Logo.png', '.'), ('CredenciaisOracle.json', '.')],
    hiddenimports=['pyautogui', 'mouseinfo', 'PIL', 'googleapiclient', 'google.oauth2', 'google_auth_oauthlib', 'pandas', 'pyperclip', 'pygetwindow', 'tkinter', 'openpyxl', 'diagnostic_helper', 'google_sheets_manager'],
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
    name='RPA_Bancada_v2',
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
    icon=['Logo.ico'],
)
