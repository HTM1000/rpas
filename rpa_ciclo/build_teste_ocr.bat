@echo off
echo ========================================
echo   BUILD TESTE OCR SIMULACAO
echo ========================================
echo.
echo Este script vai gerar um executavel standalone
echo para testar a validacao OCR SEM executar Ctrl+S
echo.

REM ========================================
REM  PRE-REQUISITOS
REM ========================================

echo [PRE] Verificando pre-requisitos...
echo.

REM Verificar se Tesseract esta instalado
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
if not exist "%TESSERACT_PATH%" (
    echo [AVISO] Tesseract-OCR nao encontrado!
    echo.
    echo O Tesseract sera incluido no executavel, mas precisara
    echo ser instalado na maquina onde o teste for executado.
    echo.
    pause
) else (
    echo    - Tesseract-OCR encontrado [OK]
)

echo.

REM ========================================
REM  LIMPEZA
REM ========================================

echo [1/4] Limpando builds anteriores...
if exist "build\teste_ocr_simulacao" rmdir /s /q "build\teste_ocr_simulacao"
if exist "dist\Teste_OCR_Simulacao.exe" del /q "dist\Teste_OCR_Simulacao.exe"
if exist "dist\tesseract" rmdir /s /q "dist\tesseract"

echo.

REM ========================================
REM  COMPILACAO
REM ========================================

echo [2/4] Compilando com PyInstaller...
python -m PyInstaller --clean teste_ocr_simulacao.spec

echo.

REM ========================================
REM  INCLUIR TESSERACT
REM ========================================

echo [3/4] Incluindo Tesseract-OCR no pacote...
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
    )

    echo    - Tesseract-OCR incluido no pacote [OK]
) else (
    echo    [AVISO] Tesseract nao encontrado
    echo    O executavel funcionara SEM OCR
)

echo.

REM ========================================
REM  VERIFICACAO FINAL
REM ========================================

echo [4/4] Verificando resultado...
if exist "dist\Teste_OCR_Simulacao.exe" (
    echo.
    echo ========================================
    echo   BUILD CONCLUIDO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\Teste_OCR_Simulacao.exe
    echo.

    if exist "dist\tesseract\tesseract.exe" (
        echo Tesseract-OCR: INCLUIDO
    ) else (
        echo Tesseract-OCR: NAO INCLUIDO
    )

    echo.
    echo IMPORTANTE:
    echo - Este executavel testa OCR SEM executar Ctrl+S
    echo - Planilha de teste: 147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY
    echo - Nao salva dados no Oracle (apenas simula)
    echo.
    echo PARA DISTRIBUIR:
    echo - Copie TODA a pasta dist\
    echo - Nao copie apenas o .exe
    echo - A pasta tesseract\ deve estar junto com o .exe
    echo - O arquivo CredenciaisOracle.json deve estar junto
    echo - O arquivo token.json sera gerado na primeira execucao
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
