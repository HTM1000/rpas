# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Coletar todas as imagens e arquivos de dados
added_files = [
    ('Logo.png', '.'),
    ('Logo.ico', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('CredenciaisOracle.json', '.'),
    ('config.json', '.'),
    # Imagens da pasta informacoes
    ('informacoes/tela-01-744x298.jpg', 'informacoes'),
    ('informacoes/tela-02-155x217-tab-enter.jpg', 'informacoes'),
    ('informacoes/tela-03-32x120.jpg', 'informacoes'),
    ('informacoes/tela-04-577x616-doubleclick.jpg', 'informacoes'),
    ('informacoes/tela-05-765x635.jpg', 'informacoes'),
    ('informacoes/tela-06-2-345x180.jpg', 'informacoes'),
    ('informacoes/tela-06-376x267.jpg', 'informacoes'),
    ('informacoes/tela-07-737x351-doubleclick.jpg', 'informacoes'),
    ('informacoes/tela-08-754x97.jpg', 'informacoes'),
    ('informacoes/wallatas.png', 'informacoes'),
]

# Importações ocultas que o PyInstaller pode não detectar automaticamente
hidden_imports = [
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.oauth2',
    'google.oauth2.credentials',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'googleapiclient',
    'googleapiclient.discovery',
    'pyautogui',
    'pyperclip',
    'keyboard',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
]

a = Analysis(
    ['RPA_Ciclo_GUI.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
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
    name='RPA_Ciclo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Não mostrar console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Logo.ico',  # Ícone do executável
)
