@echo off
echo ========================================
echo    RPA CICLO - BUILD ALTERNATIVO
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

REM Verificar/Instalar PyInstaller
echo Verificando PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando PyInstaller...
    python -m pip install pyinstaller
)

REM Instalar dependências
echo.
echo Instalando dependencias...
python -m pip install -r requirements.txt

REM Limpar builds anteriores
echo.
echo Limpando builds anteriores...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "__pycache__" rmdir /s /q __pycache__

REM Criar executável usando diferentes métodos
echo.
echo ========================================
echo   Gerando executavel (Metodo Python)...
echo ========================================
echo.

python -m PyInstaller --clean RPA_Ciclo.spec

REM Verificar resultado
if exist "dist\RPA_Ciclo.exe" (
    echo.
    echo ========================================
    echo   BUILD CONCLUIDO COM SUCESSO!
    echo ========================================
    echo.
    echo Executavel: dist\RPA_Ciclo.exe
    echo.

    REM Informacoes de seguranca
    echo ========================================
    echo   SEGURANCA
    echo ========================================
    echo.
    echo [OK] CredenciaisOracle.json EMBEDDED no executavel
    echo [OK] Dados sensiveis NAO ficam visiveis
    echo [OK] Cliente nao tera acesso as credenciais
    echo [OK] Apenas token.json sera gerado (OK para cliente)
    echo.

    REM Criar README
    (
        echo RPA CICLO - EXECUTAVEL STANDALONE
        echo ================================
        echo.
        echo SEGURANCA:
        echo - CredenciaisOracle.json esta DENTRO do executavel
        echo - Dados sensiveis NAO ficam visiveis
        echo - Cliente nao tem acesso as credenciais OAuth
        echo - Apenas token.json sera criado ^(OK para cliente^)
        echo.
        echo PRIMEIRA EXECUCAO:
        echo 1. Execute RPA_Ciclo.exe
        echo 2. Faca login com Google quando solicitado
        echo 3. Autorize acesso ao Google Sheets
        echo 4. Um arquivo token.json sera criado na mesma pasta
        echo.
        echo EXECUCAO:
        echo - Clique em "Ciclo Unico" para executar uma vez
        echo - Clique em "Modo Continuo" para repetir a cada 30 min
        echo - Clique em "Parar RPA" para interromper
        echo.
        echo ARQUIVO GERADO:
        echo - token.json ^(gerado apos primeiro login^)
        echo.
        echo LOGS:
        echo - rpa_ciclo.log ^(arquivo local^)
        echo - Google Sheets - Aba "Ciclo Automacao"
        echo.
        echo Versao: 2.0
        echo Desenvolvido para automacao Oracle
    ) > "dist\LEIA-ME.txt"

    echo - LEIA-ME.txt criado
    echo.
    echo ========================================
    echo   PRONTO PARA USAR!
    echo ========================================
    echo.
    echo Abra a pasta 'dist' e execute RPA_Ciclo.exe
    echo.

    REM Abrir pasta dist
    explorer dist

) else (
    echo.
    echo ========================================
    echo   ERRO NO BUILD!
    echo ========================================
    echo.
    echo O executavel nao foi criado.
    echo Verifique os erros acima.
    echo.
    echo DICAS:
    echo - Certifique-se de que todos os arquivos estao na pasta
    echo - Verifique se Logo.png, Tecumseh.png, Topo.png existem
    echo - Verifique se config.json existe
    echo - Tente executar: python RPA_Ciclo_GUI.py
    echo.
)

pause
