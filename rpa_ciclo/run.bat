@echo off
echo ================================
echo    RPA CICLO - Iniciando...
echo ================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.8 ou superior.
    pause
    exit /b 1
)

REM Instalar dependências se necessário
echo Verificando dependencias...
pip install -r requirements.txt --quiet

echo.
echo ================================
echo   Executando RPA CICLO
echo ================================
echo.
echo Pressione ESC para pausar
echo Pressione Ctrl+C para parar
echo.

REM Executar o script principal
python main.py

echo.
echo ================================
echo   RPA CICLO - Finalizado
echo ================================
pause
