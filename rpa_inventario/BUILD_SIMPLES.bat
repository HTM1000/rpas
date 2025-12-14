@echo off
cls

echo ===============================================================
echo          BUILD SIMPLES - RPA INVENTARIO
echo          (Assume que dependencias ja foram instaladas)
echo ===============================================================
echo.

REM ===== VERIFICAR SE PYTHON ESTA INSTALADO =====
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    pause
    exit /b 1
)

echo Python:
python --version
echo.

REM ===== VERIFICAR PYINSTALLER =====
echo Verificando PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] PyInstaller nao encontrado!
    echo        Execute: pip install pyinstaller
    pause
    exit /b 1
)
echo [OK] PyInstaller encontrado
echo.

REM ===== VERIFICAR ARQUIVOS =====
echo Verificando arquivos...
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
echo [OK] Todos os arquivos necessarios presentes
echo.

REM ===== MATAR PROCESSO =====
echo Verificando processo...
taskkill /F /IM RPA_Inventario.exe >nul 2>&1
if errorlevel 1 (
    echo [OK] Processo nao estava rodando
) else (
    echo [OK] Processo encerrado
    timeout /t 2 /nobreak >nul
)
echo.

REM ===== LIMPAR BUILD ANTERIOR =====
echo Limpando builds anteriores...
if exist "build" rmdir /S /Q build 2>nul
if exist "dist\RPA_Inventario" rmdir /S /Q dist\RPA_Inventario 2>nul
echo [OK] Limpeza concluida
echo.

REM ===== BUILD =====
echo ===============================================================
echo Iniciando build... (isso pode demorar alguns minutos)
echo ===============================================================
echo.

python -m PyInstaller --clean -y Inventario.spec

if errorlevel 1 (
    echo.
    echo [ERRO] Erro durante o build!
    pause
    exit /b 1
)

REM ===== VERIFICAR =====
echo.
echo Verificando build...
if not exist "dist\RPA_Inventario\RPA_Inventario.exe" (
    echo [ERRO] Executavel nao foi criado!
    pause
    exit /b 1
)
echo [OK] Executavel criado com sucesso
echo.

REM ===== COPIAR PARA DESKTOP =====
echo Deseja copiar para o Desktop? (S/N)
choice /C SN /N /M "S=Sim / N=Nao: "
if errorlevel 2 goto PULAR_COPIA

echo.
echo Copiando para Desktop...
xcopy "dist\RPA_Inventario" "%USERPROFILE%\Desktop\RPA_Inventario" /E /I /Y >nul
if errorlevel 1 (
    echo [AVISO] Erro ao copiar
) else (
    echo [OK] Copiado para Desktop
)
goto FIM

:PULAR_COPIA
echo [INFO] Copia ignorada

:FIM
echo.
echo ===============================================================
echo          BUILD CONCLUIDO!
echo ===============================================================
echo.
echo Localizacao: dist\RPA_Inventario\
echo.
pause
