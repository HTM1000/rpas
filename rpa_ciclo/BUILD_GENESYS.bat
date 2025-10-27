@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    BUILD GENESYS v3.0                          ║
echo ║         RPA Ciclo com Validação por Imagem                     ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo NOVO na v3.0:
echo   ✨ Validação de tela antes do preenchimento
echo   ✨ Confirmação de salvamento via imagem
echo   ✨ Detecção de queda de rede
echo.

REM ===== VERIFICAR SE PYTHON ESTÁ INSTALADO =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo    Instale Python 3.8+ e tente novamente
    pause
    exit /b 1
)

REM ===== VERIFICAR SE PYINSTALLER ESTÁ INSTALADO =====
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ PyInstaller não encontrado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo ❌ ERRO: Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
    echo ✓ PyInstaller instalado com sucesso
    echo.
)

REM ===== VERIFICAR SE AS IMAGENS EXISTEM =====
echo [1/6] Verificando imagens necessárias...
if not exist "informacoes\qtd_negativa.png" (
    echo ❌ ERRO: informacoes\qtd_negativa.png não encontrado!
    echo    Esta imagem é necessária para detectar erros do Oracle
    pause
    exit /b 1
)
if not exist "informacoes\ErroProduto.png" (
    echo ❌ ERRO: informacoes\ErroProduto.png não encontrado!
    echo    Esta imagem é necessária para detectar erros do Oracle
    pause
    exit /b 1
)
if not exist "informacoes\tempo_oracle.png" (
    echo ❌ ERRO: informacoes\tempo_oracle.png não encontrado!
    echo    Esta imagem é necessária para detectar timeout do Oracle
    pause
    exit /b 1
)
if not exist informacoes\tela_transferencia_subinventory.png (
    echo ❌ ERRO: informacoes\tela_transferencia_subinventory.png não encontrado!
    echo    Esta imagem é OBRIGATÓRIA para validação de tela (v3.0^)
    echo    Capture a tela limpa do Oracle antes de buildar
    pause
    exit /b 1
)
if not exist "informacoes\queda_rede.png" (
    echo ⚠️ AVISO: informacoes\queda_rede.png não encontrado!
    echo    Detecção de queda de rede será DESABILITADA
    echo    Recomenda-se adicionar esta imagem para melhor confiabilidade
    echo.
) else (
    echo ✓ queda_rede.png encontrada
)
echo ✓ Todas as imagens obrigatórias estão presentes
echo.

REM ===== LIMPAR BUILD ANTERIOR =====
echo [2/6] Limpando builds anteriores...
if exist "build" (
    rmdir /S /Q build
    echo ✓ Pasta build removida
)
if exist "dist\Genesys" (
    rmdir /S /Q dist\Genesys
    echo ✓ Pasta dist\Genesys removida
)
echo.

REM ===== EXECUTAR BUILD =====
echo [3/6] Iniciando build com PyInstaller...
echo.
echo ┌────────────────────────────────────────────────────────────┐
echo │ Aguarde... Este processo pode levar alguns minutos        │
echo └────────────────────────────────────────────────────────────┘
echo.

python -m PyInstaller --clean -y Genesys.spec

if errorlevel 1 (
    echo.
    echo ❌ ERRO durante o build!
    echo    Verifique os logs acima para mais detalhes
    pause
    exit /b 1
)

REM ===== VERIFICAR SE O BUILD FOI CRIADO =====
echo.
echo [4/6] Verificando build...
if not exist "dist\Genesys\Genesys.exe" (
    echo ❌ ERRO: Executável não foi criado!
    pause
    exit /b 1
)
echo ✓ Executável criado com sucesso
echo.

REM ===== VERIFICAR SE AS IMAGENS FORAM INCLUÍDAS =====
echo [5/6] Verificando imagens no build...
if not exist "dist\Genesys\_internal\informacoes\qtd_negativa.png" (
    echo ⚠️ AVISO: qtd_negativa.png não foi incluída no build!
) else (
    echo ✓ qtd_negativa.png incluída
)
if not exist "dist\Genesys\_internal\informacoes\ErroProduto.png" (
    echo ⚠️ AVISO: ErroProduto.png não foi incluída no build!
) else (
    echo ✓ ErroProduto.png incluída
)
if not exist "dist\Genesys\_internal\informacoes\tempo_oracle.png" (
    echo ⚠️ AVISO: tempo_oracle.png não foi incluída no build!
) else (
    echo ✓ tempo_oracle.png incluída
)
if not exist "dist\Genesys\_internal\informacoes\tela_transferencia_subinventory.png" (
    echo ❌ ERRO CRÍTICO: tela_transferencia_subinventory.png não foi incluída!
    echo    O RPA NÃO FUNCIONARÁ sem esta imagem!
    pause
    exit /b 1
) else (
    echo ✓ tela_transferencia_subinventory.png incluída (NOVA v3.0)
)
if not exist "dist\Genesys\_internal\informacoes\queda_rede.png" (
    echo ⚠️ AVISO: queda_rede.png não foi incluída no build
) else (
    echo ✓ queda_rede.png incluída (NOVA v3.0)
)
echo.

REM ===== COPIAR PARA DESKTOP (OPCIONAL) =====
echo [6/6] Deseja copiar para o Desktop? (S/N)
choice /C SN /N /M "Pressione S para SIM ou N para NÃO: "
if errorlevel 2 goto PULAR_COPIA
if errorlevel 1 goto FAZER_COPIA

:FAZER_COPIA
echo.
echo Copiando para C:\Users\ID135\Desktop\Genesys...
xcopy "dist\Genesys" "C:\Users\ID135\Desktop\Genesys" /E /I /Y >nul
if errorlevel 1 (
    echo ⚠️ Erro ao copiar. Verifique permissões
) else (
    echo ✓ Copiado para Desktop com sucesso
)
goto FIM

:PULAR_COPIA
echo ℹ️ Cópia para Desktop ignorada

:FIM
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                  ✓ BUILD CONCLUÍDO COM SUCESSO!                ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 📁 Localização: dist\Genesys\
echo 📦 Executável: dist\Genesys\Genesys.exe
echo.
echo ⚠️ IMPORTANTE: Distribua a PASTA COMPLETA "Genesys", não apenas o .exe
echo.
echo Arquivos incluídos:
echo   - Genesys.exe (executável principal)
echo   - _internal\ (dependências e imagens)
echo   - config.json (configurações)
echo   - CredenciaisOracle.json (credenciais Google)
echo   - Logo.png, Tecumseh.png, Topo.png
echo.
pause
