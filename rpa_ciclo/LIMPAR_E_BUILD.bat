@echo off
chcp 65001 > nul
echo ════════════════════════════════════════════════════════════════════
echo LIMPAR E RECONSTRUIR GENESYS
echo ════════════════════════════════════════════════════════════════════
echo.

echo [1/4] Matando processos do Genesys...
taskkill /F /IM Genesys.exe 2>nul
if %errorlevel% == 0 (
    echo ✓ Processo Genesys.exe finalizado
) else (
    echo ℹ Nenhum processo Genesys.exe em execução
)
echo.

echo [2/4] Aguardando 2 segundos...
timeout /t 2 /nobreak > nul
echo.

echo [3/4] Removendo pasta dist\Genesys...
if exist "dist\Genesys" (
    rmdir /S /Q "dist\Genesys"
    if %errorlevel% == 0 (
        echo ✓ Pasta removida com sucesso
    ) else (
        echo ✗ ERRO ao remover pasta - tente fechar manualmente
        echo   Caminho: %CD%\dist\Genesys
        pause
        exit /b 1
    )
) else (
    echo ℹ Pasta dist\Genesys não existe
)
echo.

echo [4/4] Executando BUILD_GENESYS.bat...
echo ════════════════════════════════════════════════════════════════════
echo.
call BUILD_GENESYS.bat
