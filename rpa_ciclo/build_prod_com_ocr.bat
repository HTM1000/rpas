@echo off
echo ========================================
echo   RPA CICLO - BUILD PRODUCAO COM OCR
echo ========================================
echo.
echo MODO: PRODUCAO (pyautogui ativo + OCR)
echo Planilha Oracle: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
echo Planilha Bancada: 1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ
echo.

REM ========================================
REM  PRE-REQUISITOS
REM ========================================

echo [PRE] Verificando pre-requisitos...
echo.

REM Verificar se Tesseract esta instalado
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
if not exist "%TESSERACT_PATH%" (
    echo [ERRO] Tesseract-OCR nao encontrado!
    echo.
    echo O Tesseract-OCR e necessario para a validacao visual (OCR).
    echo.
    echo Deseja instalar agora? (S/N)
    set /p INSTALL_TESSERACT=
    if /i "%INSTALL_TESSERACT%"=="S" (
        echo Executando instalador do Tesseract...
        call instalar_tesseract.bat
        if %ERRORLEVEL% NEQ 0 (
            echo.
            echo [ERRO] Instalacao do Tesseract falhou!
            pause
            exit /b 1
        )
    ) else (
        echo.
        echo [AVISO] Build sera feito SEM suporte a OCR!
        echo A validacao visual nao funcionara no executavel.
        echo.
        pause
    )
) else (
    echo    - Tesseract-OCR encontrado [OK]
)

echo.

REM ========================================
REM  LIMPEZA
REM ========================================

echo [1/5] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist\RPA_Ciclo_v2.exe" del /q "dist\RPA_Ciclo_v2.exe"
if exist "dist\tesseract" rmdir /s /q "dist\tesseract"
if exist "RPA_Ciclo_v2.exe" del /q "RPA_Ciclo_v2.exe"

echo.

REM ========================================
REM  VALIDACAO DE CONFIGURACOES
REM ========================================

echo [2/5] Verificando configuracoes de producao...
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

REM ========================================
REM  COMPILACAO
REM ========================================

echo [3/5] Compilando com PyInstaller...
python -m PyInstaller --clean RPA_Ciclo_v2.spec

echo.

REM ========================================
REM  INCLUIR TESSERACT NO EXECUTAVEL
REM ========================================

echo [4/5] Incluindo Tesseract-OCR no pacote standalone...
echo.

if exist "%TESSERACT_PATH%" (
    echo Copiando Tesseract-OCR para dist\tesseract\...

    REM Criar pasta tesseract dentro de dist
    if not exist "dist\tesseract" mkdir "dist\tesseract"

    REM Copiar executavel do Tesseract
    copy "%TESSERACT_PATH%" "dist\tesseract\" > nul

    REM Copiar arquivos de dados do Tesseract (tessdata)
    if exist "C:\Program Files\Tesseract-OCR\tessdata" (
        echo Copiando dados de idioma (tessdata)...
        xcopy "C:\Program Files\Tesseract-OCR\tessdata" "dist\tesseract\tessdata" /E /I /Y > nul
        echo    - tessdata copiado [OK]
    ) else (
        echo    [AVISO] tessdata nao encontrado
    )

    echo    - Tesseract-OCR incluido no pacote [OK]
) else (
    echo    [AVISO] Tesseract nao encontrado, executavel funcionara SEM OCR
)

echo.

REM ========================================
REM  VERIFICACAO FINAL
REM ========================================

echo [5/5] Verificando resultado...
if exist "dist\RPA_Ciclo_v2.exe" (
    echo.
    echo ========================================
    echo   BUILD PRODUCAO CONCLUIDO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\RPA_Ciclo_v2.exe
    echo.

    if exist "dist\tesseract\tesseract.exe" (
        echo Tesseract-OCR: INCLUIDO (validacao visual funcionara)
    ) else (
        echo Tesseract-OCR: NAO INCLUIDO (validacao visual desabilitada)
    )

    echo.
    echo IMPORTANTE:
    echo - Este executavel esta configurado para PRODUCAO
    echo - Planilha Oracle: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk
    echo - MODO_TESTE = False (pyautogui ATIVO)
    echo - OCR para validacao visual: %OCR_STATUS%
    echo.
    echo PARA DISTRIBUIR:
    echo - Copie TODA a pasta dist\
    echo - Nao copie apenas o .exe
    echo - A pasta tesseract\ deve estar junto com o .exe
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
