@echo off
cls

echo ===============================================================
echo        LIMPAR E BUILDAR RPA INVENTARIO
echo ===============================================================
echo.
echo Este script ira:
echo   1. Matar processo RPA_Inventario.exe se estiver rodando
echo   2. Limpar pastas build/ e dist/
echo   3. Limpar arquivos __pycache__
echo   4. Executar BUILD_INVENTARIO.bat
echo.

pause

echo.
echo [1/4] Matando processo RPA_Inventario.exe...
taskkill /F /IM RPA_Inventario.exe >nul 2>&1
if errorlevel 1 (
    echo [OK] Processo nao estava rodando
) else (
    echo [OK] Processo encerrado
    timeout /t 2 /nobreak >nul
)

echo.
echo [2/4] Limpando pasta build/...
if exist "build" (
    rmdir /S /Q build 2>nul
    echo [OK] Pasta build removida
) else (
    echo [INFO] Pasta build nao existe
)

echo.
echo [3/4] Limpando pasta dist/...
if exist "dist" (
    rmdir /S /Q dist 2>nul
    echo [OK] Pasta dist removida
) else (
    echo [INFO] Pasta dist nao existe
)

echo.
echo [4/4] Limpando __pycache__...
if exist "__pycache__" (
    rmdir /S /Q __pycache__ 2>nul
    echo [OK] __pycache__ removido
) else (
    echo [INFO] __pycache__ nao existe
)

echo.
echo [OK] Limpeza concluida!
echo.
echo Iniciando BUILD_INVENTARIO.bat...
echo.
timeout /t 2 /nobreak >nul

call BUILD_INVENTARIO.bat
