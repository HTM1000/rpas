@echo off
cls

echo ===============================================================
echo          TESTAR AMBIENTE - RPA INVENTARIO
echo ===============================================================
echo.

echo Testando instalacao do Python e modulos...
echo.

python --version
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)
echo.

echo Testando imports...
echo.

echo === Interface Grafica ===
python -c "import tkinter; print('[OK] tkinter instalado')"
python -c "import PIL; print('[OK] PIL/Pillow instalado - versao:', PIL.__version__)"

echo.
echo === Automacao Web (Selenium) ===
python -c "import selenium; print('[OK] selenium instalado - versao:', selenium.__version__)"
python -c "from selenium import webdriver; print('[OK] selenium.webdriver OK')"
python -c "from selenium.webdriver.common.by import By; print('[OK] selenium.webdriver.common.by OK')"
python -c "from selenium.webdriver.common.keys import Keys; print('[OK] selenium.webdriver.common.keys OK')"
python -c "import webdriver_manager; print('[OK] webdriver-manager instalado')"
python -c "from webdriver_manager.chrome import ChromeDriverManager; print('[OK] webdriver-manager.chrome OK')"

echo.
echo === Google Sheets API ===
python -c "import google.auth; print('[OK] google-auth instalado')"
python -c "from google.oauth2.credentials import Credentials; print('[OK] google.oauth2.credentials OK')"
python -c "from google_auth_oauthlib.flow import InstalledAppFlow; print('[OK] google-auth-oauthlib OK')"
python -c "from googleapiclient.discovery import build; print('[OK] google-api-python-client OK')"

echo.
echo === Outros ===
python -c "import keyboard; print('[OK] keyboard instalado')"
python -c "import pandas; print('[OK] pandas instalado')"

echo.

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] PyInstaller nao encontrado!
    echo Execute: pip install pyinstaller
) else (
    echo [OK] PyInstaller instalado
)

echo.
echo ===============================================================
echo          TESTE CONCLUIDO!
echo ===============================================================
echo.
echo Se todos os modulos aparecerem com [OK], pode fazer o build
echo Se algum falhou, execute: INSTALAR_DEPENDENCIAS.bat
echo.
pause
