@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   BUILD - RPA BANCADA LOOP INFINITO
echo ========================================
echo.

REM Verificar se PyInstaller está instalado
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] PyInstaller nao encontrado!
    echo.
    echo Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo [1/5] Verificando arquivos necessarios...
if not exist "config.json" (
    echo [ERRO] config.json nao encontrado!
    pause
    exit /b 1
)
if not exist "CredenciaisOracle.json" (
    echo [ERRO] CredenciaisOracle.json nao encontrado!
    pause
    exit /b 1
)
if not exist "RPA_Bancada.spec" (
    echo [ERRO] RPA_Bancada.spec nao encontrado!
    pause
    exit /b 1
)
echo       [OK] Todos os arquivos encontrados!
echo.

echo [2/5] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist\RPA_Bancada.exe" del /q "dist\RPA_Bancada.exe"
echo       [OK] Limpeza concluida!
echo.

echo [3/5] Executando PyInstaller...
python -m PyInstaller RPA_Bancada.spec
if errorlevel 1 (
    echo [ERRO] Build falhou!
    pause
    exit /b 1
)
echo       [OK] Build concluido!
echo.

echo [4/5] Verificando executavel...
if not exist "dist\RPA_Bancada.exe" (
    echo [ERRO] Executavel nao foi criado!
    pause
    exit /b 1
)
echo       [OK] Executavel criado com sucesso!
echo.

echo [5/5] Resumo do build:
echo.
echo   Executavel: dist\RPA_Bancada.exe
echo   Tamanho:
dir "dist\RPA_Bancada.exe" | find "RPA_Bancada.exe"
echo.
echo   Arquivos incluidos no build:
echo     - CredenciaisOracle.json
echo     - config.json
echo     - token.json (template)
echo     - Logo.png, Tecumseh.png, Topo.png
echo.

echo ========================================
echo   BUILD FINALIZADO COM SUCESSO!
echo ========================================
echo.
echo Proximos passos:
echo   1. Executar: dist\RPA_Bancada.exe
echo   2. Fazer login no Google (primeira vez)
echo   3. RPA vai entrar em loop infinito
echo.
echo Lembre-se:
echo   - Resolucao: 1440x900 (recomendado)
echo   - Oracle deve estar aberto
echo   - Menu "4. Bancada de Material" deve estar visivel
echo.
pause
