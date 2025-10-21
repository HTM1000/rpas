@echo off
echo ===============================================
echo   TESTE RPA CICLO - Modo Teste Completo
echo ===============================================
echo.
echo Este teste simula o fluxo completo:
echo   1. RPA Oracle (sem movimentos fisicos)
echo   2. RPA Bancada (dados da planilha de teste)
echo   3. Loop continuo (50 itens por vez)
echo.
echo Para parar: pressione Ctrl+C
echo.
pause
echo.
echo Iniciando teste...
echo.
python teste_ciclo.py
echo.
echo.
echo ===============================================
echo   Teste finalizado!
echo ===============================================
echo.
pause
