# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

# ========================================================================
# BANCADA LOOP - VERSAO STANDALONE v1.0
# - Extração contínua da Bancada de Material em loop infinito
# - Proteção anti-hibernação ultra-agressiva
# - Salva Excel local + Google Sheets
# - SEM processamento Oracle (apenas bancada)
# ========================================================================

# Coletar todas as imagens e arquivos de dados
added_files = [
    ('Logo.png', '.'),
    ('Logo.ico', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('CredenciaisOracle.json', '.'),
    ('config.json', '.'),
]

# Importações ocultas
hidden_imports = [
    # === MÓDULOS PRINCIPAIS ===
    'RPA_Bancada_Loop',  # CRÍTICO - módulo principal do RPA Bancada Loop

    # === GOOGLE APIs ===
    'google_sheets_manager',  # Manager de planilhas (bancada)
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.oauth2',
    'google.oauth2.credentials',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'googleapiclient',
    'googleapiclient.discovery',
    'googleapiclient.http',
    'googleapiclient.errors',

    # === AUTOMAÇÃO ===
    'pyautogui',
    'pyperclip',
    'keyboard',  # Monitoramento ESC

    # === PROCESSAMENTO DE IMAGENS ===
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',

    # === DATA PROCESSING ===
    'pandas',
    'openpyxl',

    # === SISTEMA ===
    'json',
    'datetime',
    'threading',
    'time',
    'pathlib',
]

# Módulos a excluir (reduzir tamanho do executável)
excludes_list = [
    'matplotlib',
    'scipy',
    'pytest',
    'notebook',
    'IPython',
    'cv2',  # Não precisa de OpenCV
    'pytesseract',  # Não precisa de OCR
    'numpy',  # Não precisa de numpy (OpenCV)
]

a = Analysis(
    [
        'RPA_Bancada_Loop_GUI.py',  # GUI principal
        'RPA_Bancada_Loop.py',  # Lógica principal
    ],
    pathex=[os.path.abspath('.')],  # Adicionar path atual
    binaries=[],  # Sem Tesseract
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes_list,
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
    name='Bancada_Loop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Sem console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Bancada_Loop',
)
