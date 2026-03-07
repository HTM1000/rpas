@echo off
cls

echo ===============================================================
echo          BUILD RPA INVENTARIO v1.0
echo          Build Standalone com PyAutoGUI
echo ===============================================================
echo.

REM ===== VERIFICAR SE PYTHON ESTA INSTALADO =====
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo        Instale Python 3.8+ e tente novamente
    pause
    exit /b 1
)

REM ===== INSTALAR DEPENDENCIAS =====
echo [1/6] Instalando dependencias Python...
echo.
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
    echo.
    if errorlevel 1 (
        echo [AVISO] Algumas dependencias falharam, mas continuando...
    ) else (
        echo [OK] Dependencias instaladas com sucesso
    )
    echo.
) else (
    echo [AVISO] requirements.txt nao encontrado
    echo.
)

REM ===== VERIFICAR SE PYINSTALLER ESTA INSTALADO =====
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [AVISO] PyInstaller nao encontrado. Instalando...
    python -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller
        pause
        exit /b 1
    )
    echo [OK] PyInstaller instalado com sucesso
    echo.
)

REM ===== VERIFICAR SE OS LOGOS EXISTEM =====
echo [2/6] Verificando arquivos necessarios...
if not exist "Logo.png" (
    echo [ERRO] Logo.png nao encontrado!
    pause
    exit /b 1
)
if not exist "Tecumseh.png" (
    echo [ERRO] Tecumseh.png nao encontrado!
    pause
    exit /b 1
)
if not exist "Topo.png" (
    echo [ERRO] Topo.png nao encontrado!
    pause
    exit /b 1
)
if not exist "config.json" (
    echo [ERRO] config.json nao encontrado!
    pause
    exit /b 1
)
if not exist "CredenciaisOracle.json" (
    echo [ERRO] CredenciaisOracle.json nao encontrado!
    pause
    exit /b 1
)
echo [OK] Todos os arquivos necessarios estao presentes
echo.

REM ===== VERIFICAR PASTA ELEMENTOS =====
echo [3/6] Verificando pasta elementos...
if not exist "elementos" (
    echo [ERRO] Pasta elementos nao encontrada!
    echo        Crie a pasta elementos e adicione as imagens
    pause
    exit /b 1
)

REM ===== VALIDAR IMAGENS OBRIGATORIAS =====
echo.
echo Validando imagens obrigatorias...
echo.

set MISSING=0

REM Imagens de interface (UI)
if not exist "elementos\input_nome.png" (
    echo [FALTA] elementos\input_nome.png
    set MISSING=1
)
if not exist "elementos\botao_localizar.png" (
    echo [FALTA] elementos\botao_localizar.png
    set MISSING=1
)
if not exist "elementos\botao_nao.png" (
    echo [FALTA] elementos\botao_nao.png
    set MISSING=1
)
if not exist "elementos\input_etiqueta.png" (
    echo [FALTA] elementos\input_etiqueta.png
    set MISSING=1
)
if not exist "elementos\botao_salvar.png" (
    echo [FALTA] elementos\botao_salvar.png
    set MISSING=1
)
if not exist "elementos\botao_limpar.png" (
    echo [FALTA] elementos\botao_limpar.png
    set MISSING=1
)

REM Imagens de erro (validacao)
if not exist "elementos\erro_item_inexistente.png" (
    echo [FALTA] elementos\erro_item_inexistente.png
    set MISSING=1
)
if not exist "elementos\erro_endereco_inexistente.png" (
    echo [FALTA] elementos\erro_endereco_inexistente.png
    set MISSING=1
)
if not exist "elementos\erro_subinventario_inexistente.png" (
    echo [FALTA] elementos\erro_subinventario_inexistente.png
    set MISSING=1
)
if not exist "elementos\erro_udm_inexistente.png" (
    echo [FALTA] elementos\erro_udm_inexistente.png
    set MISSING=1
)
if not exist "elementos\login_expirado.png" (
    echo [FALTA] elementos\login_expirado.png
    set MISSING=1
)

if %MISSING%==1 (
    echo.
    echo [ERRO] Imagens obrigatorias faltando!
    echo        Adicione as imagens na pasta elementos\ e tente novamente
    echo.
    choice /C SN /N /M "Continuar mesmo assim? (S para SIM, N para CANCELAR): "
    if errorlevel 2 exit /b 1
    echo [AVISO] Continuando sem todas as imagens...
) else (
    echo [OK] Todas as imagens obrigatorias presentes
)

REM Listar todas as imagens encontradas
echo.
echo Imagens que serao incluidas no build:
dir /b elementos\*.png 2>nul
echo.

REM ===== MATAR PROCESSO SE ESTIVER RODANDO =====
echo [4/6] Verificando se RPA_Inventario.exe esta rodando...
taskkill /F /IM RPA_Inventario.exe >nul 2>&1
if errorlevel 1 (
    echo [OK] Processo nao estava rodando
) else (
    echo [OK] Processo encerrado
    timeout /t 2 /nobreak >nul
)
echo.

REM ===== LIMPAR BUILD ANTERIOR =====
echo [5/6] Limpando builds anteriores...
if exist "build" (
    rmdir /S /Q build 2>nul
    if errorlevel 1 (
        echo [AVISO] Nao foi possivel remover pasta build
    ) else (
        echo [OK] Pasta build removida
    )
)
if exist "dist\RPA_Inventario" (
    rmdir /S /Q dist\RPA_Inventario 2>nul
    if errorlevel 1 (
        echo [AVISO] Nao foi possivel remover dist\RPA_Inventario
        echo         Feche todos os programas e tente novamente
        pause
        exit /b 1
    ) else (
        echo [OK] Pasta dist\RPA_Inventario removida
    )
)
echo.

REM ===== EXECUTAR BUILD =====
echo [6/6] Iniciando build com PyInstaller...
echo.
echo Aguarde... Este processo pode levar alguns minutos
echo.

python -m PyInstaller --clean -y Inventario.spec

if errorlevel 1 (
    echo.
    echo [ERRO] Erro durante o build!
    echo        Verifique os logs acima para mais detalhes
    pause
    exit /b 1
)

REM ===== VERIFICAR SE O BUILD FOI CRIADO =====
echo.
echo Verificando build...
if not exist "dist\RPA_Inventario\RPA_Inventario.exe" (
    echo [ERRO] Executavel nao foi criado!
    pause
    exit /b 1
)
echo [OK] Executavel criado com sucesso
echo.

REM ===== VERIFICAR SE PASTA ELEMENTOS FOI COPIADA =====
echo Verificando se pasta elementos foi incluida no build (_internal)...
if not exist "dist\RPA_Inventario\_internal\elementos" (
    echo [ERRO] Pasta elementos nao foi copiada para _internal!
    echo        Verifique o arquivo Inventario.spec
    pause
    exit /b 1
)

REM Contar imagens no build
set /a build_count=0
for %%f in (dist\RPA_Inventario\_internal\elementos\*.png) do set /a build_count+=1

if %build_count% LSS 5 (
    echo [AVISO] Apenas %build_count% imagens encontradas no build
    echo         Pode haver problema na copia das imagens
    pause
) else (
    echo [OK] %build_count% imagens copiadas para _internal\elementos\
)

REM Verificar imagens de erro especificas
echo.
echo Verificando imagens de validacao de erro...
set ERRO_MISSING=0

if not exist "dist\RPA_Inventario\_internal\elementos\erro_item_inexistente.png" (
    echo [FALTA] erro_item_inexistente.png
    set ERRO_MISSING=1
)
if not exist "dist\RPA_Inventario\_internal\elementos\erro_endereco_inexistente.png" (
    echo [FALTA] erro_endereco_inexistente.png
    set ERRO_MISSING=1
)
if not exist "dist\RPA_Inventario\_internal\elementos\erro_subinventario_inexistente.png" (
    echo [FALTA] erro_subinventario_inexistente.png
    set ERRO_MISSING=1
)
if not exist "dist\RPA_Inventario\_internal\elementos\erro_udm_inexistente.png" (
    echo [FALTA] erro_udm_inexistente.png
    set ERRO_MISSING=1
)
if not exist "dist\RPA_Inventario\_internal\elementos\login_expirado.png" (
    echo [FALTA] login_expirado.png
    set ERRO_MISSING=1
)

if %ERRO_MISSING%==1 (
    echo [AVISO] Algumas imagens de validacao estao faltando!
    echo         O RPA pode nao detectar erros corretamente
    pause
) else (
    echo [OK] Todas as imagens de validacao presentes
)
echo.

REM ===== COPIAR PARA DESKTOP (OPCIONAL) =====
echo Deseja copiar para o Desktop? (S/N)
choice /C SN /N /M "Pressione S para SIM ou N para NAO: "
if errorlevel 2 goto PULAR_COPIA
if errorlevel 1 goto FAZER_COPIA

:FAZER_COPIA
echo.
echo Copiando para Desktop...
xcopy "dist\RPA_Inventario" "%USERPROFILE%\Desktop\RPA_Inventario" /E /I /Y >nul
if errorlevel 1 (
    echo [AVISO] Erro ao copiar. Verifique permissoes
) else (
    echo [OK] Copiado para Desktop com sucesso
)
goto FIM

:PULAR_COPIA
echo [INFO] Copia para Desktop ignorada

:FIM
echo.
echo ===============================================================
echo          BUILD CONCLUIDO COM SUCESSO!
echo ===============================================================
echo.
echo Localizacao: dist\RPA_Inventario\
echo Executavel: dist\RPA_Inventario\RPA_Inventario.exe
echo.
echo IMPORTANTE: Distribua a PASTA COMPLETA "RPA_Inventario"
echo             nao apenas o .exe
echo.
echo Arquivos incluidos:
echo   - RPA_Inventario.exe (executavel principal)
echo   - _internal\ (dependencias PyAutoGUI, OpenCV, config, etc)
echo   - _internal\elementos\ (%build_count% imagens incluindo validacao)
echo.
echo Imagens de validacao de erro em _internal\elementos\:
echo   - erro_item_inexistente.png
echo   - erro_endereco_inexistente.png
echo   - erro_subinventario_inexistente.png
echo   - erro_udm_inexistente.png
echo   - login_expirado.png
echo.
echo NOTA: As imagens estao dentro de _internal\elementos\
echo       O executavel le automaticamente deste local
echo.
pause
