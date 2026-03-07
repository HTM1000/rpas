@echo off
chcp 65001 >nul
cls

echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    BUILD GENESYS v4.4                          ║
echo ║         RPA Ciclo com Sistema Completo de Evidências          ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo NOVO na v4.4:
echo   ✨ Detecção de Erro Centro de Custo (PRÉ e PÓS Ctrl+S)
echo.
echo Incluído desde v4.0:
echo   ✨ Internet Monitor com Circuit Breaker
echo   ✨ Screenshots PRÉ e PÓS salvamento
echo   ✨ Validação de campos vazios (estratégia simplificada)
echo   ✨ Evidências JSON completas com checksums SHA256
echo   ✨ Upload automático para Google Drive
echo   ✨ Verificação de internet ANTES de Ctrl+S (CRÍTICO!)
echo.

REM ===== DETECTAR E MUDAR PARA PASTA CORRETA =====
echo [0/9] Verificando diretório de trabalho...

REM Verificar se está na pasta essential
if exist "RPA_Ciclo_GUI_v2.py" (
    echo ✓ Já está na pasta essential
) else (
    REM Verificar se essential existe aqui
    if exist "essential\RPA_Ciclo_GUI_v2.py" (
        echo ℹ️ Mudando para pasta essential...
        cd essential
        echo ✓ Agora em: %CD%
    ) else (
        echo ❌ ERRO: Não encontrei a pasta essential!
        echo    Execute este script de:
        echo    - C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo\essential\
        echo    - OU de C:\Users\ID135\OneDrive\Desktop\www\rpas\rpa_ciclo\
        echo.
        echo    Você está em: %CD%
        pause
        exit /b 1
    )
)
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
echo [1/9] Instalando dependências Python...
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

REM ===== VERIFICAR SE OS NOVOS MÓDULOS DE EVIDÊNCIAS EXISTEM =====
echo [2/9] Verificando módulos de evidências (v4.0)...
if not exist "internet_monitor.py" (
    echo ❌ ERRO: internet_monitor.py não encontrado!
    echo    Este módulo é OBRIGATÓRIO para o sistema de evidências
    echo    Localização esperada: %CD%\internet_monitor.py
    pause
    exit /b 1
)
if not exist "screen_validator.py" (
    echo ❌ ERRO: screen_validator.py não encontrado!
    echo    Este módulo é OBRIGATÓRIO para validação de campos vazios
    echo    Localização esperada: %CD%\screen_validator.py
    pause
    exit /b 1
)
if not exist "evidencias_manager.py" (
    echo ❌ ERRO: evidencias_manager.py não encontrado!
    echo    Este módulo é OBRIGATÓRIO para gerar evidências JSON
    echo    Localização esperada: %CD%\evidencias_manager.py
    pause
    exit /b 1
)
if not exist "drive_uploader.py" (
    echo ❌ ERRO: drive_uploader.py não encontrado!
    echo    Este módulo é OBRIGATÓRIO para upload automático
    echo    Localização esperada: %CD%\drive_uploader.py
    pause
    exit /b 1
)
echo ✓ Todos os módulos de evidências encontrados
echo.

REM ===== VERIFICAR SE AS IMAGENS EXISTEM =====
echo [3/9] Verificando imagens necessárias...
if not exist "informacoes\qtd_negativa.png" (
    echo ❌ ERRO: informacoes\qtd_negativa.png não encontrado!
    echo    Localização esperada: %CD%\informacoes\qtd_negativa.png
    pause
    exit /b 1
)
if not exist "informacoes\ErroProduto.png" (
    echo ❌ ERRO: informacoes\ErroProduto.png não encontrado!
    echo    Localização esperada: %CD%\informacoes\ErroProduto.png
    pause
    exit /b 1
)
if not exist "informacoes\tempo_oracle.png" (
    echo ❌ ERRO: informacoes\tempo_oracle.png não encontrado!
    echo    Localização esperada: %CD%\informacoes\tempo_oracle.png
    pause
    exit /b 1
)
if not exist "informacoes\tela_transferencia_subinventory.png" (
    echo ⚠️ AVISO: tela_transferencia_subinventory.png - verificação falhou
    echo    Mas o PyInstaller vai tentar incluir mesmo assim...
    echo    Localização: %CD%\informacoes\tela_transferencia_subinventory.png
) else (
    echo ✓ tela_transferencia_subinventory.png encontrada! (v3.0+)
)
if not exist "informacoes\queda_rede.png" (
    echo ⚠️ AVISO: informacoes\queda_rede.png não encontrado!
    echo    Detecção de queda de rede será DESABILITADA
    echo    Recomenda-se adicionar esta imagem para melhor confiabilidade
    echo.
) else (
    echo ✓ queda_rede.png encontrada
)
if not exist "informacoes\erro_centro_custo.png" (
    echo ⚠️ AVISO: informacoes\erro_centro_custo.png não encontrado!
    echo    Detecção de erro centro de custo será DESABILITADA
    echo    Recomenda-se adicionar esta imagem (v4.4)
    echo.
) else (
    echo ✓ erro_centro_custo.png encontrada (v4.4)
)
echo ✓ Todas as imagens obrigatórias estão presentes
echo.

REM ===== VERIFICAR SE CONFIG.JSON ESTÁ ATUALIZADO =====
echo [4/9] Verificando configurações...
if not exist "config.json" (
    echo ❌ ERRO: config.json não encontrado!
    echo    Localização esperada: %CD%\config.json
    pause
    exit /b 1
)
findstr /C:"evidencias" config.json >nul 2>&1
if errorlevel 1 (
    echo ⚠️ AVISO: config.json pode não ter configurações de evidências
    echo    Sistema de evidências pode não funcionar corretamente
    echo.
) else (
    echo ✓ config.json com configurações de evidências
)
echo.

REM ===== MATAR PROCESSO SE ESTIVER RODANDO =====
echo [5/9] Verificando se Genesys.exe está rodando...
taskkill /F /IM Genesys.exe >nul 2>&1
if errorlevel 1 (
    echo ✓ Processo não estava rodando
) else (
    echo ✓ Processo encerrado
    timeout /t 2 /nobreak >nul
)
echo.

REM ===== LIMPAR BUILD ANTERIOR =====
echo [6/9] Limpando builds anteriores...
if exist "build" (
    rmdir /S /Q build 2>nul
    if errorlevel 1 (
        echo ⚠️ Não foi possível remover pasta build (pode estar em uso)
        echo    Tentando continuar mesmo assim...
    ) else (
        echo ✓ Pasta build removida
    )
)
if exist "dist\Genesys" (
    rmdir /S /Q dist\Genesys 2>nul
    if errorlevel 1 (
        echo ⚠️ Não foi possível remover dist\Genesys (pode estar em uso)
        echo    Feche todos os programas e tente novamente
        echo    Ou navegue até a pasta e delete manualmente
        pause
        exit /b 1
    ) else (
        echo ✓ Pasta dist\Genesys removida
    )
)
echo.

REM ===== EXECUTAR BUILD =====
echo [7/9] Iniciando build com PyInstaller...
echo.
echo ┌────────────────────────────────────────────────────────────┐
echo │ Aguarde... Este processo pode levar alguns minutos        │
echo │ Sistema de evidências sendo incluído (v4.0)               │
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
echo [8/9] Verificando build...
if not exist "dist\Genesys\Genesys.exe" (
    echo ❌ ERRO: Executável não foi criado!
    pause
    exit /b 1
)
echo ✓ Executável criado com sucesso
echo.

REM ===== VERIFICAR SE OS MÓDULOS FORAM INCLUÍDOS =====
echo [9/9] Verificando módulos e imagens no build...

REM Verificar módulos de evidências
if not exist "dist\Genesys\_internal\internet_monitor.py" (
    echo ⚠️ AVISO: internet_monitor.py não foi incluído no build!
) else (
    echo ✓ internet_monitor.py incluído (v4.0)
)
if not exist "dist\Genesys\_internal\screen_validator.py" (
    echo ⚠️ AVISO: screen_validator.py não foi incluído no build!
) else (
    echo ✓ screen_validator.py incluído (v4.0)
)
if not exist "dist\Genesys\_internal\evidencias_manager.py" (
    echo ⚠️ AVISO: evidencias_manager.py não foi incluído no build!
) else (
    echo ✓ evidencias_manager.py incluído (v4.0)
)
if not exist "dist\Genesys\_internal\drive_uploader.py" (
    echo ⚠️ AVISO: drive_uploader.py não foi incluído no build!
) else (
    echo ✓ drive_uploader.py incluído (v4.0)
)

REM Verificar imagens
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
    echo ⚠️ AVISO: tela_transferencia_subinventory.png - verificação falhou
    echo    Mas provavelmente foi incluída (verifique manualmente depois)
) else (
    echo ✓ tela_transferencia_subinventory.png incluída (CRÍTICO!)
)
if not exist "dist\Genesys\_internal\informacoes\queda_rede.png" (
    echo ⚠️ AVISO: queda_rede.png não foi incluída no build
) else (
    echo ✓ queda_rede.png incluída
)
if not exist "dist\Genesys\_internal\informacoes\erro_centro_custo.png" (
    echo ⚠️ AVISO: erro_centro_custo.png não foi incluída no build
) else (
    echo ✓ erro_centro_custo.png incluída (v4.4)
)
echo.

REM ===== COPIAR PARA DESKTOP (OPCIONAL) =====
echo Deseja copiar para o Desktop? (S/N)
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
echo ║                        GENESYS v4.4                            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 📁 Localização: %CD%\dist\Genesys\
echo 📦 Executável: %CD%\dist\Genesys\Genesys.exe
echo.
echo ⚠️ IMPORTANTE: Distribua a PASTA COMPLETA "Genesys", não apenas o .exe
echo.
echo Arquivos incluídos:
echo   - Genesys.exe (executável principal)
echo   - _internal\ (dependências, imagens e módulos)
echo   - config.json (configurações - incluindo evidências)
echo   - CredenciaisOracle.json (credenciais Google)
echo   - Logo.png, Tecumseh.png, Topo.png
echo.
echo 📋 NOVO na v4.4:
echo   ✓ Detecção de Erro Centro de Custo (PRÉ e PÓS Ctrl+S)
echo.
echo 📋 Sistema de Evidências v4.0:
echo   ✓ Internet Monitor com Circuit Breaker
echo   ✓ Screenshots PRÉ e PÓS salvamento
echo   ✓ Validação de campos vazios
echo   ✓ Evidências JSON com SHA256
echo   ✓ Upload automático para Google Drive
echo.
echo 🌐 Pasta de evidências será criada automaticamente:
echo   evidencias\DDMMAAAA\
echo.
echo 📤 Google Drive:
echo   https://drive.google.com/drive/folders/1SRH4yOJc2DrG0aQspAek7RMH8w6yG_Yj
echo.
pause
