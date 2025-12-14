@echo off
cls

echo ===============================================================
echo     INSTALAR DEPENDENCIAS - RPA INVENTARIO
echo ===============================================================
echo.

REM ===== VERIFICAR PYTHON =====
echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo.
    echo Por favor, instale Python 3.8 ou superior:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python encontrado
echo.

REM ===== INSTALAR DEPENDENCIAS PYTHON =====
echo [2/3] Instalando dependencias Python...
echo.

if not exist "requirements.txt" (
    echo [ERRO] requirements.txt nao encontrado!
    pause
    exit /b 1
)

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERRO] Erro ao instalar dependencias!
    echo        Verifique sua conexao com a internet
    pause
    exit /b 1
)

echo.
echo [OK] Dependencias Python instaladas com sucesso
echo.

REM ===== VERIFICAR CHROME INSTALADO =====
echo [3/3] Verificando Google Chrome...
echo.

where chrome >nul 2>&1
if errorlevel 1 (
    echo [AVISO] Google Chrome nao encontrado automaticamente
    echo         Certifique-se de que o Chrome esta instalado
    echo         O Selenium + webdriver-manager precisa do Chrome
    echo.
) else (
    echo [OK] Google Chrome encontrado
    echo.
)

echo.
echo ===============================================================
echo        INSTALACAO CONCLUIDA COM SUCESSO!
echo ===============================================================
echo.
echo Proximos passos:
echo   1. Configure o arquivo config.json com a URL do sistema
echo   2. Execute: python RPA_Inventario_GUI.py
echo   3. Ou gere o executavel com: BUILD_INVENTARIO.bat
echo.
pause
