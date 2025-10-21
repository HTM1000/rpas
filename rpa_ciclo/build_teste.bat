@echo off
chcp 65001 >nul
echo ========================================
echo BUILD DO TESTE RPA CICLO V2
echo ========================================
echo.

:: Verificar se pyinstaller está instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller não encontrado!
    echo.
    echo Instalando PyInstaller...
    pip install pyinstaller
    echo.
)

:: Limpar builds anteriores
if exist "build\Teste_RPA_Ciclo" (
    echo Limpando builds anteriores...
    rmdir /s /q "build\Teste_RPA_Ciclo"
)
if exist "dist\Teste_RPA_Ciclo.exe" (
    del /q "dist\Teste_RPA_Ciclo.exe"
)

echo.
echo Compilando teste_ciclo_completo.py...
echo.

python -m PyInstaller --name=Teste_RPA_Ciclo --onefile --console --icon=NONE --add-data="config.json;." --hidden-import=google.auth --hidden-import=google.oauth2 --hidden-import=googleapiclient --hidden-import=google_auth_oauthlib teste_ciclo_completo.py

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
echo Executavel criado em: dist\Teste_RPA_Ciclo.exe
echo.
echo Proximos passos:
echo    1. Copie dist\Teste_RPA_Ciclo.exe para onde quiser
echo    2. Certifique-se de ter config.json na mesma pasta
echo    3. Execute Teste_RPA_Ciclo.exe
echo.
pause
