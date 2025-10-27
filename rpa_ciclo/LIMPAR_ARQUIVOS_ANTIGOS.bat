@echo off
chcp 65001 >nul
echo ========================================
echo LIMPEZA DE ARQUIVOS DESNECESSÁRIOS
echo ========================================
echo.
echo Este script vai remover:
echo - Arquivos .spec antigos (exceto Genesys.spec)
echo - Arquivos Python de teste
echo - Arquivos .bat antigos
echo - Pastas build e dist antigas
echo.
pause

REM ===== REMOVER ARQUIVOS .SPEC DESNECESSÁRIOS =====
echo.
echo [1/5] Removendo arquivos .spec desnecessários...
del /Q RPA_Ciclo.spec 2>nul
del /Q RPA_Ciclo_Skip.spec 2>nul
del /Q Teste_RPA_Ciclo.spec 2>nul
del /Q teste_ocr_simulacao.spec 2>nul
del /Q RPA_Ciclo_v2.spec 2>nul
del /Q RPA_Ciclo_ONEFILE.spec 2>nul
del /Q RPA_Genesys_PRODUCAO.spec 2>nul
del /Q RPA_Genesys_TESTE.spec 2>nul
echo ✓ Arquivos .spec antigos removidos

REM ===== REMOVER ARQUIVOS PYTHON DE TESTE =====
echo.
echo [2/5] Removendo arquivos Python de teste...
del /Q main.py 2>nul
del /Q RPA_Ciclo_GUI.py 2>nul
del /Q RPA_Ciclo_Skip_GUI.py 2>nul
del /Q main_ciclo_skip.py 2>nul
del /Q teste_ciclo.py 2>nul
del /Q ativar_modo_teste.py 2>nul
del /Q main_ciclo_v2.py 2>nul
del /Q teste_ciclo_gui.py 2>nul
del /Q teste_ciclo_completo.py 2>nul
del /Q verificar_dependencias_bancada.py 2>nul
del /Q teste_ocr_simulacao.py 2>nul
del /Q main_ciclo_SEM_CTRL_S.py 2>nul
del /Q RPA_Genesys_GUI_TESTE.py 2>nul
del /Q main_ciclo_TESTE.py 2>nul
del /Q build_python.py 2>nul
echo ✓ Arquivos Python de teste removidos

REM ===== REMOVER ARQUIVOS .BAT ANTIGOS =====
echo.
echo [3/5] Removendo arquivos .bat antigos...
del /Q ativar_modo_teste.bat 2>nul
del /Q build.bat 2>nul
del /Q build_alt.bat 2>nul
del /Q build_completo_com_ocr.bat 2>nul
del /Q build_gui_v2.bat 2>nul
del /Q build_prod.bat 2>nul
del /Q build_prod_com_ocr.bat 2>nul
del /Q build_teste.bat 2>nul
del /Q build_teste_gui.bat 2>nul
del /Q build_teste_ocr.bat 2>nul
del /Q EXECUTAR_PRODUCAO.bat 2>nul
del /Q executar_teste.bat 2>nul
del /Q executar_teste_ciclo.bat 2>nul
del /Q executar_teste_gui.bat 2>nul
del /Q run.bat 2>nul
echo ✓ Arquivos .bat antigos removidos

REM ===== REMOVER TODOS OS ARQUIVOS .MD ANTIGOS =====
echo.
echo [4/6] Removendo arquivos .md antigos...

REM Remover arquivos .md específicos
del /Q MANUAL_USO.md 2>nul
del /Q SEGURANCA.md 2>nul
del /Q RESUMO_TESTE_CICLO.md 2>nul
del /Q RESUMO_IMPLEMENTACAO_TESTE.md 2>nul
del /Q TESTE_PRONTO.md 2>nul
del /Q GUIA_RAPIDO_TESTE.md 2>nul
del /Q INICIO_RAPIDO.md 2>nul
del /Q CORRECOES_TESTE.md 2>nul
del /Q CORRECOES_RATE_LIMIT.md 2>nul
del /Q LOGICA_CACHE.md 2>nul
del /Q SUMARIO_PRODUCAO.md 2>nul
del /Q CORRECAO_FINAL.md 2>nul
del /Q AJUSTES_BANCADA.md 2>nul
del /Q MONITORAMENTO_INTELIGENTE.md 2>nul
del /Q RESUMO_FINAL_AJUSTES.md 2>nul
del /Q PROCESSAMENTO_BANCADA.md 2>nul
del /Q AJUSTES_MODAL_EXPORTACAO.md 2>nul
del /Q RESUMO_COMPLETO_AJUSTES.md 2>nul
del /Q TRAVAS_VALIDACAO_IMPLEMENTADAS.md 2>nul
del /Q STANDALONE_SEM_INSTALACAO.md 2>nul
del /Q GUIA_RAPIDO_BUILD.md 2>nul
del /Q COMO_INCLUIR_TESSERACT.md 2>nul
del /Q CORRECAO_APLICADA.md 2>nul
del /Q SOLUCAO_CREDENCIAIS.md 2>nul
del /Q CORRECAO_ID_PLANILHA.md 2>nul
del /Q MELHORIAS_OCR.md 2>nul
del /Q LEIA-ME_BUILD.md 2>nul

REM Remover todos os README*.md EXCETO README_PRINCIPAL.md
for %%f in (README*.md) do (
    if /I not "%%f"=="README_PRINCIPAL.md" (
        del /Q "%%f" 2>nul
    )
)

echo ✓ Todos os .md antigos removidos (mantido: README_PRINCIPAL.md)

REM ===== REMOVER ARQUIVOS DE LOG E CACHE =====
echo.
echo [5/6] Removendo logs e cache...
del /Q *.log 2>nul
del /Q *.txt 2>nul
del /Q __pycache__\*.* 2>nul
rmdir /S /Q __pycache__ 2>nul
echo ✓ Logs e cache removidos

REM ===== LIMPAR PASTAS BUILD E DIST ANTIGAS =====
echo.
echo [6/6] Limpando pastas build e dist...
rmdir /S /Q build 2>nul
rmdir /S /Q dist 2>nul
echo ✓ Pastas build e dist limpas

echo.
echo ========================================
echo ✓ LIMPEZA CONCLUÍDA COM SUCESSO!
echo ========================================
echo.
echo Arquivos mantidos:
echo - RPA_Ciclo_GUI_v2.py (GUI principal)
echo - main_ciclo.py (lógica principal)
echo - google_sheets_ciclo.py
echo - google_sheets_manager.py
echo - mouse_position_helper.py (helper útil)
echo - Genesys.spec (arquivo de build)
echo - config.json, CredenciaisOracle.json
echo - Logos e imagens
echo - README_PRINCIPAL.md (documentação unificada)
echo - BUILD_GENESYS.bat (script de build)
echo - LIMPAR_ARQUIVOS_ANTIGOS.bat (este script)
echo.
pause
