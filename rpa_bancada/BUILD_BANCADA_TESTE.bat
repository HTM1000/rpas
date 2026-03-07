@echo off
chcp 65001 >nul
echo ============================================================
echo 🧪 BUILD RPA BANCADA - MODO TESTE
echo ============================================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (,
    echo ❌ ERRO: Python não encontrado!
    echo    Instale Python 3.8+ e adicione ao PATH
    pause
    exit /b 1
)

REM Verificar se PyInstaller está instalado
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: PyInstaller não encontrado!
    echo    Instalando PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ❌ Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
)

echo ✅ Python e PyInstaller OK
echo.

REM Verificar se config.json existe
if not exist "config.json" (
    echo ❌ ERRO: config.json não encontrado!
    echo    O arquivo config.json é necessário para o build
    pause
    exit /b 1
)

echo ✅ config.json encontrado
echo.

REM Limpar builds anteriores
echo 🧹 Limpando builds anteriores...
if exist "build\RPA_Bancada_TESTE" rmdir /s /q "build\RPA_Bancada_TESTE"
if exist "dist\RPA_Bancada_TESTE" rmdir /s /q "dist\RPA_Bancada_TESTE"
echo ✅ Limpeza concluída
echo.

REM Executar PyInstaller
echo 🔨 Compilando executável de TESTE...
echo    (Isso pode levar alguns minutos)
echo.
pyinstaller --clean --noconfirm RPA_Bancada_TESTE.spec

if errorlevel 1 (
    echo.
    echo ❌ ERRO: Build falhou!
    echo    Verifique as mensagens de erro acima
    pause
    exit /b 1
)

echo.
echo ============================================================
echo ✅ BUILD CONCLUÍDO COM SUCESSO!
echo ============================================================
echo.
echo 📁 Executável criado em:
echo    dist\RPA_Bancada_TESTE\RPA_Bancada_TESTE.exe
echo.
echo 🧪 MODO TESTE:
echo    • Cliques rápidos (sem esperas longas)
echo    • NÃO conecta Google Sheets
echo    • NÃO processa dados reais
echo    • Executa EXATAMENTE 3 ciclos e para
echo.
echo 🚀 Para testar:
echo    1. Abra o Oracle Applications
echo    2. Navegue até a tela com a Bancada de Material
echo    3. Execute: dist\RPA_Bancada_TESTE\RPA_Bancada_TESTE.exe
echo.
echo ⚠️ IMPORTANTE:
echo    • Resolução recomendada: 1440x900
echo    • FAILSAFE ativo: mova mouse para canto superior esquerdo para parar
echo.

REM Perguntar se quer abrir a pasta
set /p abrir="Deseja abrir a pasta dist? (S/N): "
if /i "%abrir%"=="S" (
    start "" "dist\RPA_Bancada_TESTE"
)

echo.
pause
