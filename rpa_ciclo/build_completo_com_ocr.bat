@echo off
REM =============================================
REM BUILD COMPLETO - RPA Ciclo v2 COM OCR
REM Inclui Tesseract automaticamente no .exe
REM =============================================

echo.
echo =============================================
echo   BUILD RPA CICLO V2 COM OCR (TESSERACT)
echo =============================================
echo.

REM 1. Verificar se Tesseract está instalado
echo [1/5] Verificando Tesseract...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo OK - Tesseract encontrado em C:\Program Files\Tesseract-OCR
    echo      Sera incluido automaticamente no executavel!
) else (
    echo.
    echo =============================================
    echo   AVISO: TESSERACT NAO ENCONTRADO!
    echo =============================================
    echo.
    echo O Tesseract nao esta instalado no sistema.
    echo O executavel sera criado SEM validacao visual ^(OCR^).
    echo.
    echo Para incluir OCR:
    echo   1. Instale Tesseract de: https://github.com/UB-Mannheim/tesseract/wiki
    echo   2. Instale em: C:\Program Files\Tesseract-OCR
    echo   3. Execute este script novamente
    echo.
    echo Deseja continuar mesmo assim? ^(S/N^)
    choice /C SN /N
    if errorlevel 2 exit /b 1
)
echo.

REM 2. Limpar builds anteriores
echo [2/5] Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
echo OK - Pastas limpas
echo.

REM 3. Executar PyInstaller
echo [3/5] Executando PyInstaller...
echo      Isso pode levar alguns minutos...
echo.
python -m PyInstaller --clean RPA_Ciclo_v2.spec

if errorlevel 1 (
    echo.
    echo =============================================
    echo   ERRO NO BUILD!
    echo =============================================
    echo.
    pause
    exit /b 1
)
echo.

REM 4. Verificar se executável foi criado
echo [4/5] Verificando executavel...
if exist "dist\RPA_Ciclo_v2.exe" (
    echo OK - RPA_Ciclo_v2.exe criado
) else (
    echo ERRO - Executavel nao encontrado
    pause
    exit /b 1
)
echo.

REM 5. Verificar se Tesseract foi incluído
echo [5/5] Verificando Tesseract no executavel...
if exist "dist\tesseract\tesseract.exe" (
    echo OK - Tesseract incluido em dist\tesseract\
    if exist "dist\tesseract\tessdata" (
        echo OK - tessdata incluido (arquivos de idioma)
        dir "dist\tesseract\tessdata\*.traineddata" | find /c ".traineddata" > temp.txt
        set /p COUNT=<temp.txt
        del temp.txt
        echo OK - Total de idiomas disponíveis
    ) else (
        echo AVISO - tessdata nao encontrado
    )
) else (
    echo AVISO - Tesseract NAO incluido (OCR desabilitado)
)
echo.

REM 6. Resumo final
echo =============================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo =============================================
echo.
echo Executavel: dist\RPA_Ciclo_v2.exe
echo.
echo Estrutura criada:
echo   dist\
echo     RPA_Ciclo_v2.exe .................... (executavel principal)
if exist "dist\tesseract\tesseract.exe" (
    echo     tesseract\
    echo       tesseract.exe ................... (OCR engine)
    echo       tessdata\ ....................... (arquivos de idioma)
    echo.
    echo NOTA: Para enviar ao cliente, envie TODA a pasta dist\
    echo       O cliente precisa copiar TUDO para area de trabalho
) else (
    echo.
    echo NOTA: Tesseract NAO incluido
    echo       Validacao visual por OCR estara desabilitada
)
echo.
echo =============================================
pause
