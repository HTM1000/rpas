@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    BUILD GENESYS TESTE v3.0                    ║
echo ║         RPA Ciclo com Validação por Imagem - TESTE            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo VERSÃO TESTE:
echo   ✨ Usa planilha de teste (147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY)
echo   ✨ Validação de tela antes do preenchimento
echo   ✨ Confirmação de salvamento via imagem
echo   ✨ Detecção de queda de rede
echo   ✨ Notificações Telegram habilitadas
echo   ✨ Tecla ESC para parar o RPA
echo.

REM ===== VERIFICAR SE PYTHON ESTÁ INSTALADO =====
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Python não encontrado!
    echo    Instale Python 3.8+ e tente novamente
    pause
    exit /b 1
)

REM ===== INSTALAR DEPENDÊNCIAS =====
echo [0/7] Instalando dependências Python...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo ⚠️ AVISO: Algumas dependências falharam, mas continuando...
    ) else (
        echo ✓ Dependências instaladas com sucesso
    )
    echo.
) else (
    echo ⚠️ requirements.txt não encontrado, pulando instalação de dependências
    echo.
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

REM ===== MATAR PROCESSO SE ESTIVER RODANDO =====
echo [2/7] Verificando se Genesys_TESTE.exe está rodando...
taskkill /F /IM Genesys_TESTE.exe >nul 2>&1
if errorlevel 1 (
    echo ✓ Processo não estava rodando
) else (
    echo ✓ Processo encerrado
    timeout /t 2 /nobreak >nul
)
echo.

REM ===== LIMPAR BUILD ANTERIOR =====
echo [3/7] Limpando builds anteriores de TESTE...
if exist "build" (
    rmdir /S /Q build 2>nul
    if errorlevel 1 (
        echo ⚠️ Não foi possível remover pasta build (pode estar em uso)
        echo    Tentando continuar mesmo assim...
    ) else (
        echo ✓ Pasta build removida
    )
)
if exist "dist\Genesys_TESTE" (
    rmdir /S /Q dist\Genesys_TESTE 2>nul
    if errorlevel 1 (
        echo ⚠️ Não foi possível remover dist\Genesys_TESTE (pode estar em uso)
        echo    Feche todos os programas e tente novamente
        echo    Ou navegue até a pasta e delete manualmente
        pause
        exit /b 1
    ) else (
        echo ✓ Pasta dist\Genesys_TESTE removida
    )
)
echo.

REM ===== EXECUTAR BUILD =====
echo [4/7] Iniciando build TESTE com PyInstaller...
echo.
echo ┌────────────────────────────────────────────────────────────┐
echo │ Aguarde... Este processo pode levar alguns minutos        │
echo └────────────────────────────────────────────────────────────┘
echo.

python -m PyInstaller --clean -y Genesys_TESTE.spec

if errorlevel 1 (
    echo.
    echo ❌ ERRO durante o build!
    echo    Verifique os logs acima para mais detalhes
    pause
    exit /b 1
)

REM ===== VERIFICAR SE O BUILD FOI CRIADO =====
echo.
echo [5/7] Verificando build TESTE...
if not exist "dist\Genesys_TESTE\Genesys_TESTE.exe" (
    echo ❌ ERRO: Executável TESTE não foi criado!
    pause
    exit /b 1
)
echo ✓ Executável TESTE criado com sucesso
echo.

REM ===== VERIFICAR SE AS IMAGENS FORAM INCLUÍDAS =====
echo [6/7] Verificando imagens no build TESTE...
if not exist "dist\Genesys_TESTE\_internal\informacoes\qtd_negativa.png" (
    echo ⚠️ AVISO: qtd_negativa.png não foi incluída no build!
) else (
    echo ✓ qtd_negativa.png incluída
)
if not exist "dist\Genesys_TESTE\_internal\informacoes\ErroProduto.png" (
    echo ⚠️ AVISO: ErroProduto.png não foi incluída no build!
) else (
    echo ✓ ErroProduto.png incluída
)
if not exist "dist\Genesys_TESTE\_internal\informacoes\tempo_oracle.png" (
    echo ⚠️ AVISO: tempo_oracle.png não foi incluída no build!
) else (
    echo ✓ tempo_oracle.png incluída
)
if not exist "dist\Genesys_TESTE\_internal\informacoes\tela_transferencia_subinventory.png" (
    echo ❌ ERRO CRÍTICO: tela_transferencia_subinventory.png não foi incluída!
    echo    O RPA NÃO FUNCIONARÁ sem esta imagem!
    pause
    exit /b 1
) else (
    echo ✓ tela_transferencia_subinventory.png incluída (NOVA v3.0)
)
if not exist "dist\Genesys_TESTE\_internal\informacoes\queda_rede.png" (
    echo ⚠️ AVISO: queda_rede.png não foi incluída no build
) else (
    echo ✓ queda_rede.png incluída (NOVA v3.0)
)
echo.

REM ===== COPIAR PARA DESKTOP (OPCIONAL) =====
echo [7/7] Deseja copiar para o Desktop? (S/N)
choice /C SN /N /M "Pressione S para SIM ou N para NÃO: "
if errorlevel 2 goto PULAR_COPIA
if errorlevel 1 goto FAZER_COPIA

:FAZER_COPIA
echo.
echo Copiando para C:\Users\ID135\Desktop\Genesys_TESTE...
xcopy "dist\Genesys_TESTE" "C:\Users\ID135\Desktop\Genesys_TESTE" /E /I /Y >nul
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
echo ║          ✓ BUILD TESTE CONCLUÍDO COM SUCESSO!                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 📁 Localização: dist\Genesys_TESTE\
echo 📦 Executável: dist\Genesys_TESTE\Genesys_TESTE.exe
echo.
echo ⚠️ IMPORTANTE: Distribua a PASTA COMPLETA "Genesys_TESTE", não apenas o .exe
echo.
echo Arquivos incluídos:
echo   - Genesys_TESTE.exe (executável principal - VERSÃO TESTE)
echo   - _internal\ (dependências e imagens)
echo   - config.json (configurações)
echo   - CredenciaisOracle.json (credenciais Google)
echo   - Logo.png, Tecumseh.png, Topo.png
echo.
echo 🔥 DIFERENÇAS DA VERSÃO TESTE:
echo   - Usa planilha de teste (147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY)
echo   - Cache separado (processados.json)
echo   - Notificações Telegram habilitadas
echo   - ESC para parar funcionando
echo.
pause
