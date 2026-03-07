# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

block_cipher = None

# ========================================================================
# RPA INVENTÁRIO - BUILD STANDALONE COM PYAUTOGUI
# Versão: 1.0
# ========================================================================

# Coletar arquivos de dados (logos, config, etc)
added_files = [
    ('Logo.png', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('config.json', '.'),
    ('CredenciaisOracle.json', '.'),  # Credenciais Google OAuth
]

# Adicionar ícone se existir
if os.path.exists('Logo.ico'):
    added_files.append(('Logo.ico', '.'))

# Coletar TODAS as imagens da pasta elementos/ para _internal
elementos_dir = Path('elementos')
if elementos_dir.exists():
    print(f"[OK] Coletando imagens da pasta elementos/...")
    elementos_count = 0
    for img in elementos_dir.glob('*.png'):
        # Formato: (source, destination_folder_inside_MEIPASS)
        # Isso cria _internal/elementos/ automaticamente
        added_files.append((str(img), 'elementos'))
        elementos_count += 1
        print(f"     - {img.name}")
    print(f"[OK] {elementos_count} imagens adicionadas para _internal/elementos/")
else:
    print(f"[WARN] Pasta elementos/ não encontrada!")

# Coletar TODAS as imagens da pasta elementos/teste/ (MODO TESTE)
elementos_teste_dir = Path('elementos/teste')
if elementos_teste_dir.exists():
    print(f"[OK] Coletando imagens da pasta elementos/teste/ (MODO TESTE)...")
    teste_count = 0
    for img in elementos_teste_dir.glob('*.png'):
        # Isso cria _internal/elementos/teste/
        added_files.append((str(img), 'elementos/teste'))
        teste_count += 1
        print(f"     - {img.name}")
    print(f"[OK] {teste_count} imagens adicionadas para _internal/elementos/teste/")
else:
    print(f"[WARN] Pasta elementos/teste/ não encontrada! (Modo Teste não disponível)")

# ========================================================================
# PYAUTOGUI - CONFIGURAÇÃO
# Coleta dados do PyAutoGUI e dependências de imagem
# ========================================================================

pyautogui_datas = []
pyautogui_binaries = []
pyautogui_hiddenimports = []

try:
    # Coletar PyAutoGUI
    pag_datas, pag_binaries, pag_hiddenimports = collect_all('pyautogui')
    pyautogui_datas.extend(pag_datas)
    pyautogui_binaries.extend(pag_binaries)
    pyautogui_hiddenimports.extend(pag_hiddenimports)

    print(f"[OK] PyAutoGUI coletado via collect_all")
    print(f"     - {len(pag_datas)} arquivos de dados")
    print(f"     - {len(pag_binaries)} binarios")
    print(f"     - {len(pag_hiddenimports)} imports ocultos")

except Exception as e:
    print(f"[WARN] Erro ao coletar PyAutoGUI: {e}")

# ========================================================================
# OPENCV - Para detecção de imagens
# ========================================================================

cv2_datas = []
cv2_binaries = []
cv2_hiddenimports = []

try:
    cv2_datas, cv2_binaries, cv2_hiddenimports = collect_all('cv2')

    print(f"[OK] OpenCV coletado")
    print(f"     - {len(cv2_datas)} arquivos de dados")

except Exception as e:
    print(f"[WARN] Erro ao coletar OpenCV: {e}")

# ========================================================================
# IMPORTAÇÕES OCULTAS
# ========================================================================

hidden_imports = [
    'main_inventario',  # Módulo principal do RPA
    'google_sheets_inventario',  # Módulo Google Sheets
    'keyboard',  # Controle de teclado (ESC)
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'pandas',
    'json',
    # PyAutoGUI e dependências
    'pyautogui',
    'pyperclip',
    'pymsgbox',
    'pytweening',
    'pyscreeze',
    'mouseinfo',
    # OpenCV para detecção de imagem
    'cv2',
    'numpy',
    # Google API
    'google',
    'google.auth',
    'google.auth.transport',
    'google.auth.transport.requests',
    'google.oauth2',
    'google.oauth2.credentials',
    'google_auth_oauthlib',
    'google_auth_oauthlib.flow',
    'googleapiclient',
    'googleapiclient.discovery',
]

# Adicionar os hidden imports coletados automaticamente
hidden_imports.extend(pyautogui_hiddenimports)
hidden_imports.extend(cv2_hiddenimports)

# ========================================================================
# MÓDULOS A EXCLUIR (para reduzir tamanho)
# ========================================================================

excludes_list = [
    'matplotlib',
    'scipy',
    'pytest',
    'notebook',
    'IPython',
]

# Combinar todas as datas e binaries
all_datas = added_files + pyautogui_datas + cv2_datas
all_binaries = pyautogui_binaries + cv2_binaries

# ========================================================================
# ANÁLISE E BUILD
# ========================================================================

a = Analysis(
    ['RPA_Inventario_GUI.py', 'main_inventario.py', 'google_sheets_inventario.py'],
    pathex=[os.path.abspath('.')],
    binaries=all_binaries,
    datas=all_datas,
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

# ========================================================================
# MODO ONEDIR (RECOMENDADO)
# Gera uma pasta com o executável e dependências
# ========================================================================

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='RPA_Inventario',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Logo.ico' if os.path.exists('Logo.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='RPA_Inventario',
)
