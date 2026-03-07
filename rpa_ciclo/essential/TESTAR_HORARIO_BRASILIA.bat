@echo off
chcp 65001 >nul
echo ============================================================
echo 🕐 TESTE DE HORÁRIO - BRASÍLIA (UTC-3)
echo ============================================================
echo.
echo Este script vai enviar dados fictícios para sua planilha
echo para você verificar se o horário está correto
echo.
echo Planilha de teste:
echo https://docs.google.com/spreadsheets/d/1fjkU2kSG6A91-lCD1FDcIiZobyBpcB_Vqquo8Meptvg
echo.
echo ============================================================
echo.

python teste_horario_brasilia.py

echo.
pause
