# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path

block_cipher = None

# ========================================================================
# GENESYS - VERSAO PRODUCAO v4.0 (COM Sistema Completo de Evidências)
# - OCR/Tesseract HABILITADO para validação visual dos campos
# - OpenCV incluído para confidence na detecção de imagens
# - Atalho ESC para parar o RPA
# - Validação de tela antes do preenchimento (tela_transferencia_subinventory.png)
# - Detecção de queda de rede (queda_rede.png)
# - Sistema de Evidências com:
#   * Internet Monitor com Circuit Breaker
#   * Screenshots PRÉ e PÓS salvamento
#   * Validação de campos vazios
#   * Evidências JSON completas com SHA256
#   * Upload automático para Google Drive
# ========================================================================

# Coletar todas as imagens e arquivos de dados
added_files = [
    ('Logo.png', '.'),
    ('Logo.ico', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('CredenciaisOracle.json', '.'),
    ('config.json', '.'),

    # === NOVOS MÓDULOS DE EVIDÊNCIAS (v4.0) ===
    ('internet_monitor.py', '.'),
    ('screen_validator.py', '.'),
    ('evidencias_manager.py', '.'),
    ('drive_uploader.py', '.'),

    # Imagens para detecção de erros do Oracle - NA RAIZ (igual RPA_Oracle)
    ('informacoes/qtd_negativa.png', '.'),
    ('informacoes/ErroProduto.png', '.'),
    ('informacoes/tempo_oracle.png', '.'),
    ('informacoes/erro_centro_custo.png', '.'),  # v4.4 - Modal erro centro de custo

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
    ('informacoes/erro_centro_custo.png', 'informacoes'),  # v4.4 - Modal erro centro de custo
    ('informacoes/erro_item_inexistente.png', 'informacoes'),    # Modal item não encontrado
    ('informacoes/erro_endereco_inexistente.png', 'informacoes'), # Modal endereço não encontrado
    ('informacoes/erro_subinv_inexistente.png', 'informacoes'),  # Modal subinventário não encontrado

    # IMAGENS - Validação por imagem (v3.0+)
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

    print(f"[OK] Tesseract será incluído no build: {tesseract_path}")
else:
    print(f"[WARN] Tesseract não encontrado em: {tesseract_path}")

# Importações ocultas
hidden_imports = [
    # === MÓDULOS PRINCIPAIS ===
    'main_ciclo',  # CRÍTICO - módulo principal do RPA Ciclo
    'validador_hibrido',  # Sistema de validação híbrida
    'telegram_notifier',  # Notificações via Telegram

    # === SISTEMA DE EVIDÊNCIAS (v4.0) ===
    'internet_monitor',  # Monitor de internet com circuit breaker
    'screen_validator',  # Validação visual com OCR
    'evidencias_manager',  # Gerenciador de evidências JSON
    'drive_uploader',  # Upload automático para Google Drive

    # === GOOGLE APIs ===
    'google_sheets_ciclo',  # Integração Google Sheets
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
    'googleapiclient.http',  # Para MediaFileUpload (Drive)
    'googleapiclient.errors',  # Para HttpError (Drive)

    # === AUTOMAÇÃO ===
    'pyautogui',
    'pyperclip',
    'keyboard',  # Monitoramento ESC

    # === PROCESSAMENTO DE IMAGENS E OCR ===
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageGrab',  # OCR - captura de tela
    'PIL.ImageEnhance',  # OCR - processamento de imagem
    'cv2',  # OpenCV para confidence na detecção de imagem
    'numpy',  # Necessário para OpenCV e análise de pixels
    'pytesseract',  # OCR para validação visual

    # === DATA PROCESSING ===
    'pandas',
    'openpyxl',

    # === NETWORKING ===
    'requests',  # Para Telegram API
    'socket',  # Para verificação de internet

    # === SISTEMA ===
    'psutil',  # Monitoramento de sistema (preparado para futuro)
    'hashlib',  # Para checksums SHA256
    'json',
    'datetime',
    'threading',
]

# Módulos a excluir
excludes_list = [
    'matplotlib',
    'scipy',
    'pytest',
    'notebook',
    'IPython',
]

# Combinar datas (imagens + tesseract)
all_datas = added_files + tesseract_datas

a = Analysis(
    [
        'RPA_Ciclo_GUI_v2.py',  # GUI principal
        'main_ciclo.py',  # Lógica principal
        'validador_hibrido.py',  # Validação híbrida
        'telegram_notifier.py',  # Telegram
        'internet_monitor.py',  # Monitor de internet
        'screen_validator.py',  # Validador de tela
        'evidencias_manager.py',  # Gerenciador de evidências
        'drive_uploader.py',  # Upload Drive
    ],
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
    name='Genesys',
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
    name='Genesys',
)
