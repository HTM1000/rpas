@echo off
echo ============================================
echo       TESTE DO RPA ORACLE
echo ============================================
echo.
echo Este teste vai:
echo 1. Conectar na planilha de teste
echo 2. Buscar linhas prontas (Status=CONCLUIDO)
echo 3. Processar e gravar em Excel
echo 4. Atualizar Status Oracle na planilha
echo.
echo Pressione qualquer tecla para iniciar...
pause > nul

python teste_rpa.py

echo.
echo ============================================
echo Teste finalizado!
echo.
echo Arquivos gerados:
echo - dados_processados.xlsx (dados processados)
echo - cache_teste.json (IDs pendentes)
echo ============================================
echo.
pause
