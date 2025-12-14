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

REM Contar imagens PNG na pasta elementos
set /a count=0
for %%f in (elementos\*.png) do set /a count+=1

if %count% LSS 5 (
    echo [AVISO] Apenas %count% imagens encontradas na pasta elementos
    echo         Esperado pelo menos 5 imagens:
    echo         - input_nome.png
    echo         - botao_localizar.png
    echo         - botao_nao.png
    echo         - input_etiqueta.png
    echo         - botao_salvar.png
    echo.
    choice /C SN /N /M "Continuar mesmo assim? (S/N): "
    if errorlevel 2 exit /b 1
) else (
    echo [OK] %count% imagens encontradas na pasta elementos
)
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
echo   - _internal\ (dependencias PyAutoGUI, OpenCV, etc)
echo   - elementos\ (imagens para deteccao de elementos)
echo   - config.json (configuracoes)
echo   - CredenciaisOracle.json (credenciais Google)
echo   - Logo.png, Tecumseh.png, Topo.png
echo.
pause
