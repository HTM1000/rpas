# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

# ========================================================================
# GENESYS - VERSAO TESTE v3.0 (COM Validação por Imagem)
# - OCR/Tesseract HABILITADO para validação visual dos campos
# - OpenCV incluído para confidence na detecção de imagens
# - Atalho ESC para parar o RPA
# - Validação de tela antes do preenchimento (tela_transferencia_subinventory.png)
# - Detecção de queda de rede (queda_rede.png)
# - Confirmação de salvamento via imagem (não mais via clipboard)
# - USA PLANILHA DE TESTE: 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
# ========================================================================

# Coletar todas as imagens e arquivos de dados
added_files = [
    ('Logo.png', '.'),
    ('Logo.ico', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('CredenciaisOracle.json', '.'),
    ('config_TESTE.json', '.'),  # <<<< VERSÃO TESTE - Usa planilha de teste
    ('IS_TEST_MODE.flag', '.'),  # <<<< FLAG para ativar modo TESTE
    # Imagens para detecção de erros do Oracle - NA RAIZ (igual RPA_Oracle)
    ('informacoes/qtd_negativa.png', '.'),
    ('informacoes/ErroProduto.png', '.'),
    ('informacoes/tempo_oracle.png', '.'),
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
    # Imagens para detecção de erros do Oracle - TAMBÉM em informacoes/ (fallback)
    ('informacoes/qtd_negativa.png', 'informacoes'),
    ('informacoes/ErroProduto.png', 'informacoes'),
    ('informacoes/tempo_oracle.png', 'informacoes'),
    # NOVAS IMAGENS - Validação por imagem (v3.0)
    ('informacoes/tela_transferencia_subinventory.png', 'informacoes'),  # Validação de tela correta
    ('informacoes/queda_rede.png', 'informacoes'),  # Detecção de queda de internet
]

# ========================================================================
# TESSERACT OCR - CONFIGURAÇÃO
# Incluir Tesseract e tessdata para validação visual
# ========================================================================

# Caminho do Tesseract instalado
tesseract_path = Path(r'C:\Program Files\Tesseract-OCR')
tesseract_binaries = []
tesseract_datas = []

if tesseract_path.exists():
    # Adicionar executável do Tesseract
    tesseract_binaries.append((str(tesseract_path / 'tesseract.exe'), 'tesseract'))

    # Adicionar tessdata (idiomas OCR)
    tessdata_dir = tesseract_path / 'tessdata'
    if tessdata_dir.exists():
        for arquivo in tessdata_dir.glob('*'):
            tesseract_datas.append((str(arquivo), 'tesseract/tessdata'))

    print(f"[OK] Tesseract será incluído no build TESTE: {tesseract_path}")
else:
    print(f"[WARN] Tesseract não encontrado em: {tesseract_path}")

# Importações ocultas
hidden_imports = [
    'main_ciclo',  # CRÍTICO - módulo principal do RPA Ciclo
    'validador_hibrido',  # NOVO - Sistema de validação híbrida (substitui OCR)
    'telegram_notifier',  # NOVO - Notificações via Telegram
    'google_sheets_ciclo_TESTE',  # <<<< VERSÃO TESTE da integração Google Sheets
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
    'pyautogui',
    'pyperclip',
    'keyboard',  # Monitoramento ESC
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageGrab',  # OCR - captura de tela
    'PIL.ImageEnhance',  # OCR - processamento de imagem
    'pandas',
    'cv2',  # OpenCV para confidence na detecção de imagem
    'numpy',  # Necessário para OpenCV e análise de pixels
    'pytesseract',  # OCR para validação visual (mantido como fallback)
    'requests',  # Para Telegram API
]

# Módulos a excluir
excludes_list = [
    # cv2 e opencv REMOVIDOS - necessários para confidence na detecção de imagem
    'matplotlib',
    'scipy',
    'pytest',
    'notebook',
    'IPython',
]

# Combinar datas (imagens + tesseract)
all_datas = added_files + tesseract_datas

a = Analysis(
    ['RPA_Ciclo_GUI_v2.py', 'main_ciclo.py', 'validador_hibrido.py', 'telegram_notifier.py', 'google_sheets_ciclo_TESTE.py'],  # Incluir versão TESTE
    pathex=[os.path.abspath('.')],  # Adicionar path atual
    binaries=tesseract_binaries,
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Genesys_TESTE',  # <<<< NOME DO EXECUTÁVEL DE TESTE
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
    name='Genesys_TESTE',  # <<<< NOME DA PASTA DE TESTE
)
