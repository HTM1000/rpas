@echo off
echo ========================================
echo   RPA CICLO v2 - Build Script
echo ========================================
echo.
echo Iniciando compilacao do executavel...
echo.

REM Limpar builds anteriores
echo [1/3] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "RPA_Ciclo_v2.exe" del /q "RPA_Ciclo_v2.exe"

echo.
echo [2/3] Compilando com PyInstaller...
python -m PyInstaller --clean RPA_Ciclo_v2.spec

echo.
echo [3/3] Verificando resultado...
if exist "dist\RPA_Ciclo_v2.exe" (
    echo.
    echo ========================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\RPA_Ciclo_v2.exe
    echo.
    echo Pressione qualquer tecla para abrir a pasta dist...
    pause > nul
    explorer dist
) else (
    echo.
    echo ========================================
    echo   ERRO NA COMPILACAO!
    echo ========================================
    echo.
    echo O executavel nao foi criado.
    echo Verifique os erros acima.
    echo.
    pause
)
