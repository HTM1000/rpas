@echo off
echo ========================================
echo   INSTALADOR TESSERACT-OCR
echo ========================================
echo.
echo Este script ira baixar e instalar o Tesseract-OCR
echo necessario para a validacao visual (OCR) do RPA Ciclo.
echo.
echo Pressione qualquer tecla para continuar ou CTRL+C para cancelar...
pause > nul
echo.

REM Criar pasta temporaria
set TEMP_DIR=%TEMP%\tesseract_install
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

REM URL do instalador do Tesseract (versao 5.x para Windows 64-bit)
set TESSERACT_URL=https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe
set INSTALLER_PATH=%TEMP_DIR%\tesseract-installer.exe

echo [1/4] Baixando Tesseract-OCR...
echo URL: %TESSERACT_URL%
echo.

REM Baixar usando PowerShell (nativo do Windows)
powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%TESSERACT_URL%' -OutFile '%INSTALLER_PATH%'}"

if not exist "%INSTALLER_PATH%" (
    echo.
    echo [ERRO] Falha ao baixar o instalador!
    echo.
    echo Tente baixar manualmente de:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
)

echo.
echo [2/4] Instalador baixado com sucesso!
echo Tamanho do arquivo:
dir "%INSTALLER_PATH%" | find ".exe"
echo.
echo [3/4] Iniciando instalador do Tesseract-OCR...
echo.
echo IMPORTANTE:
echo - Aceite todas as opcoes padrao
echo - Certifique-se de instalar em: C:\Program Files\Tesseract-OCR
echo - Marque a opcao para adicionar ao PATH (se disponivel)
echo.
pause

REM Executar instalador (modo interativo)
start /wait "" "%INSTALLER_PATH%"

echo.
echo [4/4] Verificando instalacao...
echo.

REM Verificar se foi instalado
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ========================================
    echo   INSTALACAO CONCLUIDA!
    echo ========================================
    echo.
    echo Tesseract-OCR foi instalado em:
    echo C:\Program Files\Tesseract-OCR\tesseract.exe
    echo.
    echo Agora voce pode compilar o RPA_Ciclo com suporte a OCR!
    echo.

    REM Adicionar ao PATH do usuario
    echo Deseja adicionar Tesseract ao PATH do sistema? (S/N)
    set /p ADD_PATH=
    if /i "%ADD_PATH%"=="S" (
        echo Adicionando ao PATH...
        setx PATH "%PATH%;C:\Program Files\Tesseract-OCR" > nul
        echo PATH atualizado! Reinicie o terminal para aplicar.
    )

    echo.
    echo Pressione qualquer tecla para limpar arquivos temporarios...
    pause > nul

    REM Limpar arquivos temporarios
    del /q "%INSTALLER_PATH%"
    rmdir "%TEMP_DIR%"

    echo.
    echo Instalacao concluida com sucesso!
    pause
) else (
    echo ========================================
    echo   ERRO NA INSTALACAO!
    echo ========================================
    echo.
    echo Tesseract-OCR nao foi encontrado em:
    echo C:\Program Files\Tesseract-OCR\tesseract.exe
    echo.
    echo Verifique se a instalacao foi concluida corretamente.
    echo.
    echo Caso o problema persista, baixe e instale manualmente:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    pause
    exit /b 1
)
