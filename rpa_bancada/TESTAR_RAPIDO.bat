@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 RPA BANCADA - TESTE RÁPIDO (Python direto)
echo ============================================================
echo.
echo ⚙️ Este script executa o teste SEM compilar
echo    (mais rápido para validação de coordenadas)
echo.
echo ⏳ Aguardando 3 segundos para você posicionar as janelas...
echo.

timeout /t 3 /nobreak >nul

echo 🚀 INICIANDO TESTE...
echo.

python main_teste.py

echo.
pause
