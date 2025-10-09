@echo off
echo ========================================
echo   RPA NFRi - Preparar Distribuicao
echo ========================================
echo.

REM Criar pasta de distribuição
set DIST_FOLDER=RPA_NFRi_Distribuicao
if exist "%DIST_FOLDER%" rmdir /s /q "%DIST_FOLDER%"
mkdir "%DIST_FOLDER%"

echo [1/4] Copiando executavel...
copy "dist\RPA_NFRi.exe" "%DIST_FOLDER%\" >nul
if errorlevel 1 (
    echo ERRO: Executavel nao encontrado! Execute build.bat primeiro.
    pause
    exit /b 1
)

echo [2/4] Copiando credenciais...
copy "CredenciaisOracle.json" "%DIST_FOLDER%\" >nul
if errorlevel 1 (
    echo AVISO: CredenciaisOracle.json nao encontrado. Copie manualmente!
)

echo [3/4] Copiando token (se existir)...
if exist "token.json" (
    copy "token.json" "%DIST_FOLDER%\" >nul
    echo Token copiado! O usuario nao precisara fazer login.
) else (
    echo Token nao encontrado. Usuario precisara fazer login na primeira vez.
)

echo [4/4] Criando arquivo de instrucoes...
(
echo ========================================
echo   RPA NFRi - Instrucoes de Uso
echo ========================================
echo.
echo IMPORTANTE: Coloque todos os arquivos na mesma pasta!
echo.
echo ARQUIVOS NECESSARIOS:
echo   - RPA_NFRi.exe
echo   - CredenciaisOracle.json
echo   - token.json ^(opcional - evita login^)
echo.
echo COMO USAR:
echo   1. Abra o sistema web no navegador
echo   2. Execute RPA_NFRi.exe
echo   3. Clique em "Iniciar"
echo   4. Pressione ESC para pausar
echo.
echo PRIMEIRA EXECUCAO:
echo   - Se nao tiver token.json, uma janela do navegador
echo     abrira para fazer login no Google
echo   - Apos o login, um arquivo token.json sera criado
echo     automaticamente
echo.
echo PLANILHA DESTINO:
echo   https://docs.google.com/spreadsheets/d/1GnHcBKhXWKfU4Pcucyqj1_Vv9jiIkbY4iJ4prugD9ZE/edit
echo.
echo ========================================
) > "%DIST_FOLDER%\LEIA-ME.txt"

echo.
echo ========================================
echo   PREPARACAO CONCLUIDA!
echo ========================================
echo.
echo Pasta criada: %DIST_FOLDER%
echo.
echo Arquivos incluidos:
dir "%DIST_FOLDER%" /b
echo.
echo PROXIMOS PASSOS:
echo   1. Verifique se CredenciaisOracle.json foi copiado
echo   2. Compacte a pasta "%DIST_FOLDER%" em .zip
echo   3. Distribua o arquivo .zip
echo.

pause
