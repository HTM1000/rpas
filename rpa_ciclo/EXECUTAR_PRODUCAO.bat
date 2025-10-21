@echo off
cls
echo ========================================
echo   RPA CICLO v2.0 - PRODUCAO
echo ========================================
echo.
echo   Modo: PRODUCAO (PyAutoGUI ATIVO)
echo   Planilha Oracle: 14yUMc12i... (PROD)
echo   Planilha Bancada: 1UgJWxmn... (PROD)
echo.
echo ========================================
echo.
echo Executando RPA_Ciclo_v2.exe...
echo.

cd "%~dp0dist"
start RPA_Ciclo_v2.exe

echo.
echo RPA_Ciclo_v2.exe iniciado!
echo.
echo IMPORTANTE:
echo - NAO MEXA no mouse/teclado durante execucao
echo - Use FAILSAFE (mouse no canto) para parar
echo - Ou clique no botao "Parar RPA"
echo.
pause
