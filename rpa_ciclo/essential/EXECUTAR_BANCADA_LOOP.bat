@echo off
title RPA Bancada Loop - Execucao
color 0A
echo.
echo ===============================================
echo  RPA BANCADA LOOP - Extracao Continua
echo ===============================================
echo.
echo Iniciando aplicacao...
echo.

cd /d "%~dp0"

python RPA_Bancada_Loop.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERRO ao executar o script!
    echo.
    pause
)
