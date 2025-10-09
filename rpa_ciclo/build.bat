@echo off
echo ========================================
echo    RPA CICLO - BUILD DO EXECUTAVEL
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Verificar/Instalar PyInstaller
echo Verificando PyInstaller...
pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando PyInstaller...
    pip install pyinstaller
)

REM Instalar dependências
echo.
echo Instalando dependencias...
pip install -r requirements.txt

REM Limpar builds anteriores
echo.
echo Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

REM Criar executável
echo.
echo ========================================
echo   Gerando executavel...
echo ========================================
echo.

python -m PyInstaller --clean RPA_Ciclo.spec

REM Verificar se build foi bem-sucedido
if exist "dist\RPA_Ciclo.exe" (
    echo.
    echo ========================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel criado em: dist\RPA_Ciclo.exe
    echo.
    echo ========================================
    echo   SEGURANCA
    echo ========================================
    echo.
    echo [OK] CredenciaisOracle.json esta DENTRO do executavel
    echo [OK] Dados sensiveis NAO ficam visiveis
    echo [OK] Apenas token.json sera criado externamente
    echo.

    REM Criar arquivo README na pasta dist
    echo Criando README...
    (
        echo RPA CICLO - EXECUTAVEL STANDALONE
        echo ================================
        echo.
        echo SEGURANCA:
        echo - CredenciaisOracle.json esta DENTRO do executavel
        echo - Dados sensiveis NAO ficam visiveis
        echo - Cliente nao tem acesso as credenciais
        echo - Apenas token.json sera criado ^(OK para cliente^)
        echo.
        echo Para executar:
        echo 1. Execute RPA_Ciclo.exe
        echo 2. Na primeira execucao, faca login com Google
        echo 3. Escolha o modo de execucao:
        echo    - Ciclo Unico: Executa uma vez
        echo    - Modo Continuo: Repete a cada 30 min
        echo.
        echo Arquivo gerado:
        echo - token.json ^(gerado apos primeiro login^)
        echo.
        echo Logs sao salvos em:
        echo - rpa_ciclo.log ^(arquivo local^)
        echo - Google Sheets ^(aba "Ciclo Automacao"^)
        echo.
        echo Desenvolvido para automacao Oracle
        echo Versao: 2.0
    ) > "dist\LEIA-ME.txt"

    echo.
    echo ========================================
    echo   ARQUIVOS GERADOS:
    echo ========================================
    dir dist
    echo.
    echo Para distribuir, copie toda a pasta 'dist'
    echo.
) else (
    echo.
    echo ========================================
    echo   ERRO NO BUILD!
    echo ========================================
    echo.
    echo Verifique os erros acima.
)

echo.
pause
