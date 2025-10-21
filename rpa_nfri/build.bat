@echo off
echo ========================================
echo   RPA NFRi - Build Executavel
echo ========================================
echo.

REM Limpar builds anteriores
echo [1/3] Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist RPA_NFRi.spec.bak del RPA_NFRi.spec.bak

echo.
echo [2/3] Gerando executavel com PyInstaller...
python -m PyInstaller RPA_NFRi.spec

echo.
echo [3/3] Verificando resultado...
if exist "dist\RPA_NFRi.exe" (
    echo.
    echo ========================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\RPA_NFRi.exe
    echo.
    echo IMPORTANTE: Nao se esqueca de:
    echo   1. Copiar o arquivo CredenciaisOracle.json para a mesma pasta do .exe
    echo   2. Na primeira execucao, fazer login no Google para gerar token.json
    echo.
) else (
    echo.
    echo ========================================
    echo   ERRO NO BUILD!
    echo ========================================
    echo.
)

pause
