@echo off
chcp 65001 >nul
echo ========================================
echo BUILD DO TESTE RPA CICLO V2 (GUI)
echo ========================================
echo.

:: Verificar se pyinstaller está instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller nao encontrado!
    echo.
    echo Instalando PyInstaller...
    pip install pyinstaller
    echo.
)

:: Limpar builds anteriores
if exist "build\Teste_RPA_Ciclo_GUI" (
    echo Limpando builds anteriores...
    rmdir /s /q "build\Teste_RPA_Ciclo_GUI"
)
if exist "dist\Teste_RPA_Ciclo_GUI.exe" (
    del /q "dist\Teste_RPA_Ciclo_GUI.exe"
)

echo.
echo Compilando teste_ciclo_gui.py com interface grafica...
echo.

python -m PyInstaller --name=Teste_RPA_Ciclo_GUI --onefile --windowed --icon=NONE --add-data="config.json;." --hidden-import=google.auth --hidden-import=google.oauth2 --hidden-import=googleapiclient --hidden-import=google_auth_oauthlib teste_ciclo_gui.py

if errorlevel 1 (
    echo.
    echo Erro durante a compilacao!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD CONCLUIDO COM SUCESSO!
echo ========================================
echo.
echo Executavel criado em: dist\Teste_RPA_Ciclo_GUI.exe
echo.
echo Proximos passos:
echo    1. Execute dist\Teste_RPA_Ciclo_GUI.exe
echo    2. Use a interface grafica para controlar o teste
echo    3. Acompanhe os logs em tempo real
echo.
echo DICA: Este executavel abre uma janela (nao e console)
echo.
pause
