@echo off
chcp 65001 >nul 2>&1
cls
title BUILD BANCADA LOOP - Executavel Standalone
color 0E

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   BUILD BANCADA LOOP - Sistema de Extracao Continua
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo   Este script vai criar o executavel standalone Bancada_Loop.exe
echo   com todas as dependencias embutidas.
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Python nao encontrado!
    echo        Instale Python 3.8+ e tente novamente.
    pause
    exit /b 1
)

echo [OK] Python encontrado:
python --version
echo.

REM Verificar se PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] PyInstaller nao encontrado!
    echo        Instalando PyInstaller...
    python -m pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao instalar PyInstaller!
        pause
        exit /b 1
    )
)

echo [OK] PyInstaller encontrado
echo.

REM Verificar arquivos obrigatórios
echo ───────────────────────────────────────────────────────────────────────────
echo Verificando arquivos obrigatorios...
echo ───────────────────────────────────────────────────────────────────────────
echo.

set "ARQUIVOS_OK=1"

if not exist "RPA_Bancada_Loop_GUI.py" (
    echo [X] RPA_Bancada_Loop_GUI.py NAO encontrado!
    set "ARQUIVOS_OK=0"
) else (
    echo [OK] RPA_Bancada_Loop_GUI.py
)

if not exist "RPA_Bancada_Loop.py" (
    echo [X] RPA_Bancada_Loop.py NAO encontrado!
    set "ARQUIVOS_OK=0"
) else (
    echo [OK] RPA_Bancada_Loop.py
)

if not exist "google_sheets_manager.py" (
    echo [X] google_sheets_manager.py NAO encontrado!
    set "ARQUIVOS_OK=0"
) else (
    echo [OK] google_sheets_manager.py
)

if not exist "CredenciaisOracle.json" (
    echo [X] CredenciaisOracle.json NAO encontrado!
    set "ARQUIVOS_OK=0"
) else (
    echo [OK] CredenciaisOracle.json
)

if not exist "config.json" (
    echo [X] config.json NAO encontrado!
    set "ARQUIVOS_OK=0"
) else (
    echo [OK] config.json
)

if not exist "Logo.png" (
    echo [!] Logo.png NAO encontrado (opcional)
) else (
    echo [OK] Logo.png
)

if not exist "Logo.ico" (
    echo [!] Logo.ico NAO encontrado (opcional)
) else (
    echo [OK] Logo.ico
)

if not exist "Tecumseh.png" (
    echo [!] Tecumseh.png NAO encontrado (opcional)
) else (
    echo [OK] Tecumseh.png
)

if not exist "Topo.png" (
    echo [!] Topo.png NAO encontrado (opcional)
) else (
    echo [OK] Topo.png
)

echo.

if "%ARQUIVOS_OK%"=="0" (
    echo [ERRO] Arquivos obrigatorios faltando!
    echo        Certifique-se que todos os arquivos estao no diretorio.
    pause
    exit /b 1
)

echo ───────────────────────────────────────────────────────────────────────────
echo Todos os arquivos obrigatorios encontrados!
echo ───────────────────────────────────────────────────────────────────────────
echo.

REM Limpar builds anteriores
echo Limpando builds anteriores...
echo.

if exist "build\" (
    echo [LIMPANDO] build\
    rmdir /s /q "build" >nul 2>&1
)

if exist "dist\Bancada_Loop\" (
    echo [LIMPANDO] dist\Bancada_Loop\
    rmdir /s /q "dist\Bancada_Loop" >nul 2>&1
)

if exist "Bancada_Loop.spec" (
    echo [ENCONTRADO] Bancada_Loop.spec (usando arquivo existente)
) else (
    echo [AVISO] Bancada_Loop.spec nao encontrado!
    echo         Certifique-se que o arquivo .spec existe.
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   INICIANDO BUILD COM PYINSTALLER
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Executar PyInstaller
python -m PyInstaller Bancada_Loop.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ═══════════════════════════════════════════════════════════════════════════
    echo [ERRO] Build falhou!
    echo ═══════════════════════════════════════════════════════════════════════════
    echo.
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   VALIDANDO BUILD
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Verificar se executável foi criado
if not exist "dist\Bancada_Loop\Bancada_Loop.exe" (
    echo [ERRO] Executavel nao foi criado!
    echo        Verifique os logs acima para detalhes do erro.
    pause
    exit /b 1
)

echo [OK] Executavel criado: dist\Bancada_Loop\Bancada_Loop.exe
echo.

REM Verificar arquivos importantes
if not exist "dist\Bancada_Loop\_internal\" (
    echo [AVISO] Pasta _internal nao encontrada
) else (
    echo [OK] Pasta _internal encontrada
)

if not exist "dist\Bancada_Loop\config.json" (
    echo [AVISO] config.json nao encontrado no build
) else (
    echo [OK] config.json encontrado
)

if not exist "dist\Bancada_Loop\CredenciaisOracle.json" (
    echo [AVISO] CredenciaisOracle.json nao encontrado no build
) else (
    echo [OK] CredenciaisOracle.json encontrado
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   BUILD CONCLUIDO COM SUCESSO!
echo ═══════════════════════════════════════════════════════════════════════════
echo.
echo   Executavel criado em:
echo   dist\Bancada_Loop\Bancada_Loop.exe
echo.
echo   IMPORTANTE:
echo   - Distribua a pasta COMPLETA: dist\Bancada_Loop\
echo   - Nao distribua apenas o .exe!
echo   - O executavel depende dos arquivos em _internal\
echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo.

REM Perguntar se deseja copiar para Desktop
echo.
set /p COPIAR_DESKTOP="Deseja copiar a pasta para o Desktop? (S/N): "

if /i "%COPIAR_DESKTOP%"=="S" (
    echo.
    echo Copiando para Desktop...

    set "DESKTOP=%USERPROFILE%\Desktop"

    if exist "%DESKTOP%\Bancada_Loop\" (
        echo [LIMPANDO] Versao antiga no Desktop...
        rmdir /s /q "%DESKTOP%\Bancada_Loop" >nul 2>&1
    )

    xcopy "dist\Bancada_Loop" "%DESKTOP%\Bancada_Loop\" /E /I /Y >nul 2>&1

    if %ERRORLEVEL% EQU 0 (
        echo [OK] Copiado para: %DESKTOP%\Bancada_Loop\
        echo.
        echo Voce pode executar:
        echo %DESKTOP%\Bancada_Loop\Bancada_Loop.exe
    ) else (
        echo [ERRO] Falha ao copiar para Desktop
    )
)

echo.
echo ═══════════════════════════════════════════════════════════════════════════
echo   PRONTO!
echo ═══════════════════════════════════════════════════════════════════════════
echo.

pause
