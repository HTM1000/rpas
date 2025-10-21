@echo off
echo ========================================
echo   RPA CICLO - BUILD PRODUCAO
echo ========================================
echo.
echo MODO: PRODUCAO (pyautogui ativo)
echo Planilha Oracle: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
echo Planilha Bancada: 1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ
echo.
echo Iniciando compilacao do executavel de PRODUCAO...
echo.

REM Limpar builds anteriores
echo [1/4] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist\RPA_Ciclo_v2.exe" del /q "dist\RPA_Ciclo_v2.exe"
if exist "RPA_Ciclo_v2.exe" del /q "RPA_Ciclo_v2.exe"

echo.
echo [2/4] Verificando configuracoes de producao...
findstr /C:"MODO_TESTE = False" main_ciclo.py > nul
if %ERRORLEVEL% EQU 0 (
    echo    - MODO_TESTE = False [OK]
) else (
    echo    [ERRO] MODO_TESTE nao esta configurado como False!
    echo    Por favor, edite main_ciclo.py e altere MODO_TESTE para False
    pause
    exit /b 1
)

findstr /C:"14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk" main_ciclo.py > nul
if %ERRORLEVEL% EQU 0 (
    echo    - Planilha Oracle PRODUCAO [OK]
) else (
    echo    [AVISO] Planilha Oracle pode nao estar configurada para producao!
)

echo.
echo [3/4] Compilando com PyInstaller...
python -m PyInstaller --clean RPA_Ciclo_v2.spec

echo.
echo [4/4] Verificando resultado...
if exist "dist\RPA_Ciclo_v2.exe" (
    echo.
    echo ========================================
    echo   BUILD PRODUCAO CONCLUIDO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\RPA_Ciclo_v2.exe
    echo.
    echo IMPORTANTE:
    echo - Este executavel esta configurado para PRODUCAO
    echo - Planilha Oracle: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
    echo - MODO_TESTE = False (pyautogui ATIVO)
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
