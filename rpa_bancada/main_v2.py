# -*- coding: utf-8 -*-
"""
Versão melhorada do main.py com sistema de diagnóstico robusto
"""

import time
from io import StringIO
from pathlib import Path
import threading
import sys
import os
import re

import pyautogui as pag
import pyperclip
import pandas as pd

# Importar módulo de diagnóstico
from diagnostic_helper import OracleDiagnostic

# Importar Google Sheets manager
try:
    from google_sheets_manager import enviar_para_google_sheets
    GOOGLE_SHEETS_AVAILABLE = True
    print("[OK] Google Sheets manager importado com sucesso")
except ImportError as e:
    print(f"[WARN] Google Sheets nao disponivel: {e}")
    GOOGLE_SHEETS_AVAILABLE = False

# Focar janela
try:
    from pygetwindow import getWindowsWithTitle
except Exception:
    getWindowsWithTitle = None

# =================== CONFIG ===================
BASE = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))
OUT = (BASE / "out"); OUT.mkdir(exist_ok=True)

# ===== COORDENADAS FIXAS =====
COORD_DETALHADO = (273, 358)
COORD_LOCALIZAR = (524, 689)
COORD_ORG_CELL  = (318, 174)

# ===== CONFIGURAÇÕES DE TIMING AJUSTADAS =====
pag.FAILSAFE = True
pag.PAUSE = 0.35
MOUSE_MOVE_DUR = 0.45
SLEEP_POS_CLIQUE = 0.8
SLEEP_ABERTURA = 1.2

# Tempo máximo de espera para Oracle (20 minutos)
ORACLE_MAX_WAIT = 20 * 60

# =================== VARIÁVEIS GLOBAIS ===================
_rpa_running = False
_gui_log_callback = None
_keep_awake_stop = threading.Event()
_keep_awake_thread = None
_diagnostic = None

# =================== HELPERS ===================

def set_gui_log_callback(callback):
    """Define callback para enviar logs para a GUI"""
    global _gui_log_callback, _diagnostic
    _gui_log_callback = callback
    # Criar instância do diagnóstico com o callback
    _diagnostic = OracleDiagnostic(log_callback=callback)

def gui_log(msg):
    """Envia log para GUI se callback estiver definido"""
    if _gui_log_callback:
        _gui_log_callback(msg)
    else:
        print(msg)

def focus_oracle():
    """Tenta focar a janela do Oracle"""
    if not getWindowsWithTitle:
        return
    titles = [
        "Aplicativos Oracle", "Oracle Applications",
        "Tecumseh PROD Upgraded", "Bancada de Material"
    ]
    for t in titles:
        wins = getWindowsWithTitle(t)
        if wins:
            try:
                wins[0].activate()
                time.sleep(0.8)
                return
            except Exception:
                pass

def move_click(x, y, right=False):
    """Move o mouse e clica"""
    pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
    pag.click(button='right' if right else 'left')
    time.sleep(SLEEP_POS_CLIQUE)

def mapear_colunas_inteligente(df):
    """
    Sistema de mapeamento mais inteligente e flexível
    """
    gui_log(f"🔍 Iniciando mapeamento inteligente de {len(df.columns)} colunas")
    
    # Dicionário de mapeamento com múltiplas variações
    mapeamentos = {
        'ORG.': ['org.', 'org', 'organization', 'organização', 'organizacao'],
        'SUB.': ['sub.', 'sub', 'subinventory', 'subinventário', 'subinventario'],
        'ENDEREÇO': ['endereço', 'endereco', 'endereÇo', 'address', 'locator', 'local', 'localizador'],
        'ITEM': ['item', 'código', 'codigo', 'product', 'produto', 'sku'],
        'DESCRIÇÃO ITEM': ['descrição do item', 'descrição item', 'descricao do item', 
                          'descricao item', 'descrição', 'descricao', 'description', 
                          'item description', 'desc item'],
        'REV.': ['rev.', 'rev', 'revision', 'revisão', 'revisao'],
        'UDM PRINCIPAL': ['udm principal', 'udm', 'uom', 'unit', 'unidade', 
                         'unidade de medida', 'unit of measure'],
        'EM ESTOQUE': ['em estoque', 'estoque', 'quantity', 'quantidade', 'qty', 
                      'qtd', 'qtde', 'stock', 'inventory']
    }
    
    colunas_mapeadas = {}
    colunas_originais = list(df.columns)
    
    # Primeiro, tentar mapeamento exato
    for col_original in colunas_originais:
        col_limpa = str(col_original).strip()
        
        # Verificar mapeamento direto
        for col_padrao, variacoes in mapeamentos.items():
            # Comparação case-insensitive
            if col_limpa.lower() in variacoes or col_limpa.lower() == col_padrao.lower():
                colunas_mapeadas[col_original] = col_padrao
                gui_log(f"   ✓ Mapeado: '{col_original}' → '{col_padrao}'")
                break
                
    # Se não encontrou todas as colunas, tentar fuzzy matching
    if len(colunas_mapeadas) < 8:
        gui_log("⚠️ Nem todas as colunas foram mapeadas, tentando fuzzy matching...")
        
        for col_original in colunas_originais:
            if col_original not in colunas_mapeadas:
                col_limpa = re.sub(r'[^\w\s]', '', str(col_original).strip().lower())
                
                for col_padrao, variacoes in mapeamentos.items():
                    for variacao in variacoes:
                        variacao_limpa = re.sub(r'[^\w\s]', '', variacao.lower())
                        
                        # Verificar se contém a palavra-chave
                        if variacao_limpa in col_limpa or col_limpa in variacao_limpa:
                            colunas_mapeadas[col_original] = col_padrao
                            gui_log(f"   ✓ Fuzzy match: '{col_original}' → '{col_padrao}'")
                            break
                    
                    if col_original in colunas_mapeadas:
                        break
    
    gui_log(f"📊 Total mapeado: {len(colunas_mapeadas)}/{len(mapeamentos)} colunas")
    
    if len(colunas_mapeadas) == 0:
        gui_log("❌ ERRO CRÍTICO: Nenhuma coluna foi mapeada!")
        return pd.DataFrame()
    
    # Renomear colunas
    df_renamed = df.rename(columns=colunas_mapeadas)
    
    # Selecionar apenas as colunas mapeadas
    colunas_finais = ['ORG.', 'SUB.', 'ENDEREÇO', 'ITEM', 'DESCRIÇÃO ITEM', 'REV.', 'UDM PRINCIPAL', 'EM ESTOQUE']
    colunas_disponiveis = [col for col in colunas_finais if col in df_renamed.columns]
    
    if len(colunas_disponiveis) < 4:  # Mínimo de 4 colunas para considerar válido
        gui_log(f"⚠️ Apenas {len(colunas_disponiveis)} colunas encontradas, mínimo é 4")
        return df  # Retorna DataFrame original para análise
    
    # Criar DataFrame com colunas disponíveis, preenchendo as faltantes
    df_final = pd.DataFrame()
    for col in colunas_finais:
        if col in df_renamed.columns:
            df_final[col] = df_renamed[col]
        else:
            df_final[col] = ''  # Coluna vazia para as faltantes
            gui_log(f"   ⚠️ Coluna '{col}' não encontrada, preenchida com vazio")
    
    # Limpar dados
    df_final = df_final.fillna('')
    
    gui_log(f"✅ DataFrame final: {df_final.shape[0]} linhas x {df_final.shape[1]} colunas")
    return df_final

def processar_clipboard_robusto(texto):
    """
    Processamento robusto do clipboard usando múltiplas estratégias
    """
    global _diagnostic
    
    if not _diagnostic:
        _diagnostic = OracleDiagnostic(log_callback=gui_log)
    
    gui_log(f"🔧 Processando {len(texto):,} caracteres do clipboard")
    
    # Analisar conteúdo
    analysis = _diagnostic.analyze_clipboard_content(texto)
    gui_log(f"📊 Análise: {analysis['lines']} linhas, {analysis['tabs']} tabs, separador: {analysis['detected_separator']}")
    
    # Tentar múltiplas estratégias
    results = _diagnostic.try_multiple_parsing_strategies(texto)
    
    if not results:
        gui_log("❌ Nenhuma estratégia de parsing funcionou!")
        return pd.DataFrame()
    
    # Escolher melhor resultado baseado em validação
    best_df = None
    best_score = 0
    best_strategy = None
    
    for strategy, df in results:
        validation = _diagnostic.validate_dataframe(df)
        
        if validation['is_valid'] and validation['validity_score'] > best_score:
            best_df = df
            best_score = validation['validity_score']
            best_strategy = strategy
    
    if best_df is not None:
        gui_log(f"✅ Melhor estratégia: {best_strategy} (score: {best_score:.2%})")
        
        # Aplicar mapeamento inteligente
        df_mapeado = mapear_colunas_inteligente(best_df)
        
        if not df_mapeado.empty:
            return df_mapeado
        else:
            # Se mapeamento falhou, retornar o melhor DataFrame sem mapeamento
            gui_log("⚠️ Mapeamento falhou, retornando dados brutos")
            return best_df
    else:
        gui_log("❌ Nenhum DataFrame válido encontrado")
        
        # Como última tentativa, retornar o primeiro resultado
        if results:
            strategy, df = results[0]
            gui_log(f"⚠️ Usando fallback: {strategy}")
            return df
    
    return pd.DataFrame()

def salvar_com_fallback(df):
    """
    Salva DataFrame com múltiplas estratégias de fallback
    """
    hoje = pd.Timestamp.now().strftime("%Y-%m-%d_%H%M")
    xlsx = OUT / f"export-{hoje}.xlsx"
    
    try:
        # Tentar salvar normalmente
        df.to_excel(xlsx, index=False, engine='openpyxl')
        gui_log(f"✅ Excel salvo: {xlsx}")
        return str(xlsx)
    except Exception as e:
        gui_log(f"⚠️ Erro salvando Excel: {e}")
        
        # Fallback 1: Salvar como CSV
        try:
            csv_file = OUT / f"export-{hoje}.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            gui_log(f"✅ CSV salvo como fallback: {csv_file}")
            return str(csv_file)
        except Exception as e2:
            gui_log(f"❌ Erro salvando CSV: {e2}")
            
        # Fallback 2: Salvar como TSV
        try:
            tsv_file = OUT / f"export-{hoje}.tsv"
            df.to_csv(tsv_file, sep='\t', index=False, encoding='utf-8')
            gui_log(f"✅ TSV salvo como fallback: {tsv_file}")
            return str(tsv_file)
        except Exception as e3:
            gui_log(f"❌ Erro salvando TSV: {e3}")
    
    return None

# =================== KEEP-AWAKE ===================
def keep_awake_loop(stop_event, interval=50):
    """Thread keep-awake"""
    while not stop_event.is_set():
        pag.keyDown('shift')
        pag.keyUp('shift')
        for _ in range(int(interval * 10)):
            if stop_event.is_set():
                break
            time.sleep(0.1)

# =================== CONTROLE ===================
def stop_rpa():
    """Para o RPA"""
    global _rpa_running
    _rpa_running = False
    _keep_awake_stop.set()

def is_rpa_running():
    """Verifica se está rodando"""
    return _rpa_running

# =================== CICLO PRINCIPAL ===================
def run_once():
    """Executa um ciclo completo com diagnóstico robusto"""
    global _diagnostic
    
    if not _rpa_running:
        return False
    
    if not _diagnostic:
        _diagnostic = OracleDiagnostic(log_callback=gui_log)
    
    gui_log("="*60)
    gui_log("🚀 INICIANDO NOVO CICLO DE EXTRAÇÃO")
    gui_log("="*60)
    
    # Criar nova sessão de diagnóstico
    _diagnostic = OracleDiagnostic(log_callback=gui_log)
    
    focus_oracle()
    
    # 1) Clicar em "Detalhado"
    gui_log("🖱️ [1/8] Clicando em 'Detalhado'...")
    move_click(*COORD_DETALHADO)
    
    if not _rpa_running:
        return False
    
    # 2) Clicar em "Localizar"
    gui_log("🖱️ [2/8] Clicando em 'Localizar'...")
    move_click(*COORD_LOCALIZAR)

    # DELAY AUMENTADO: Aguardar processamento do Oracle (pode levar até 3 minutos)
    gui_log("⏳ Aguardando processamento do Localizar (até 3 minutos)...")
    time.sleep(180)  # 3 minutos para garantir que o Oracle processou

    focus_oracle()

    if not _rpa_running:
        return False

    # DELAY ADICIONAL: Garantir que a grid está completamente carregada
    gui_log("⏳ Aguardando carregamento completo da grid...")
    time.sleep(10)  # Delay extra para garantir que a grid carregou

    # 3) Clicar na célula Org
    gui_log("🖱️ [3/8] Clicando na célula Org...")
    move_click(*COORD_ORG_CELL)
    
    if not _rpa_running:
        return False
    
    # 4) Limpar clipboard
    gui_log("🧹 [4/8] Limpando clipboard...")
    pyperclip.copy('')
    time.sleep(0.5)
    
    # 5) Abrir menu
    gui_log("⌨️ [5/8] Abrindo menu de contexto...")
    pag.hotkey('shift', 'f10')
    time.sleep(1.5)
    
    focus_oracle()
    
    # 6) Navegar e selecionar "Copiar Todas as Linhas"
    gui_log("⌨️ [6/8] Selecionando 'Copiar Todas as Linhas'...")
    for _ in range(3):  # Navegar menu
        pag.press('down')
        time.sleep(0.25)
    pag.press('enter')

    # DELAY AUMENTADO: Aguardar que os dados sejam copiados para o clipboard
    gui_log("⏳ Aguardando cópia dos dados para o clipboard (30 segundos)...")
    time.sleep(30)  # Delay maior para garantir que todos os dados foram copiados

    if not _rpa_running:
        return False

    # 7) MONITORAMENTO DO CLIPBOARD COM RETRY OTIMIZADO
    gui_log("👀 [7/8] Verificando clipboard...")

    texto_final = None
    max_tentativas_retry = 3
    tempo_espera_clipboard = 60  # Esperar 60 segundos para clipboard ter dados

    for tentativa in range(max_tentativas_retry):
        if tentativa == 0:
            gui_log(f"⏳ Tentativa {tentativa + 1}/{max_tentativas_retry} - Aguardando dados no clipboard...")
        else:
            gui_log(f"🔄 Tentativa {tentativa + 1}/{max_tentativas_retry} de recuperação...")

            # Clicar no botão cancelar (872, 667)
            gui_log("🖱️ Clicando em 'Cancelar'...")
            move_click(872, 667)
            time.sleep(2)

            # Clicar em (322, 307)
            gui_log("🖱️ Clicando em posição (322, 307)...")
            move_click(322, 307)
            time.sleep(2)

            # Repetir ação de copiar com botão direito
            gui_log("🧹 Limpando clipboard...")
            pyperclip.copy('')
            time.sleep(0.5)

            gui_log("🖱️ Clicando na célula Org novamente...")
            move_click(*COORD_ORG_CELL)
            time.sleep(0.5)

            gui_log("⌨️ Abrindo menu de contexto...")
            pag.hotkey('shift', 'f10')
            time.sleep(1.5)

            focus_oracle()

            gui_log("⌨️ Selecionando 'Copiar Todas as Linhas'...")
            for _ in range(3):
                pag.press('down')
                time.sleep(0.25)
            pag.press('enter')

            gui_log("⏳ Aguardando cópia dos dados...")
            time.sleep(30)

        # Aguardar tempo curto para verificar se clipboard tem dados
        tempo_verificado = 0
        intervalo_verificacao = 5  # Verificar a cada 5 segundos

        while tempo_verificado < tempo_espera_clipboard and _rpa_running:
            time.sleep(intervalo_verificacao)
            tempo_verificado += intervalo_verificacao

            texto_atual = pyperclip.paste()

            if texto_atual and len(texto_atual.strip()) > 50:  # Clipboard com dados válidos
                texto_final = texto_atual
                gui_log(f"✅ Dados obtidos no clipboard ({len(texto_final):,} caracteres)")
                break
            else:
                gui_log(f"⏳ Aguardando dados... ({tempo_verificado}/{tempo_espera_clipboard}s)")

        # Verificar se obteve dados
        if texto_final and len(texto_final.strip()) > 50:
            gui_log(f"✅ Clipboard preenchido com sucesso na tentativa {tentativa + 1}")
            break
        else:
            gui_log(f"❌ Tentativa {tentativa + 1} falhou - clipboard vazio ou com poucos dados")

            if tentativa < max_tentativas_retry - 1:
                gui_log("⏳ Preparando próxima tentativa...")
            else:
                gui_log(f"❌ ERRO: Todas as {max_tentativas_retry} tentativas falharam")
                gui_log("🔄 Tentando monitoramento estendido como última opção...")

                # Última tentativa: usar monitoramento longo (até 5 minutos)
                texto_final, sucesso_longo = _diagnostic.monitor_clipboard_changes(
                    max_duration=300,  # 5 minutos
                    check_interval=5
                )

                if not texto_final or len(texto_final.strip()) < 50:
                    gui_log("❌ Monitoramento estendido também falhou")
                    _diagnostic.create_diagnostic_report()
                    return False

    if not texto_final:
        gui_log("❌ ERRO: Clipboard vazio após todas as tentativas")
        _diagnostic.create_diagnostic_report()
        return False

    # 8) PROCESSAR DADOS
    gui_log("🔄 [8/8] Processando dados extraídos...")

    # Usar processamento robusto
    df = processar_clipboard_robusto(texto_final)
    
    if df.empty:
        gui_log("❌ DataFrame vazio após processamento")
        _diagnostic.create_diagnostic_report()
        return False
    
    gui_log(f"✅ Dados processados: {df.shape[0]:,} linhas x {df.shape[1]} colunas")
    
    # Salvar localmente com fallback
    arquivo_salvo = salvar_com_fallback(df)
    
    if arquivo_salvo:
        gui_log(f"💾 Dados salvos localmente: {arquivo_salvo}")
    else:
        gui_log("⚠️ Falha ao salvar localmente")
    
    # Tentar enviar para Google Sheets
    if GOOGLE_SHEETS_AVAILABLE and not df.empty:
        try:
            gui_log("☁️ Enviando para Google Sheets...")
            sucesso_sheets = enviar_para_google_sheets(df)
            
            if sucesso_sheets:
                gui_log("✅ Dados enviados para Google Sheets!")
            else:
                gui_log("❌ Falha no envio para Google Sheets")
        except Exception as e:
            gui_log(f"❌ Erro no Google Sheets: {e}")
    
    # Criar relatório de diagnóstico
    report_file = _diagnostic.create_diagnostic_report()
    gui_log(f"📊 Relatório de diagnóstico: {report_file}")
    
    return arquivo_salvo is not None

# =================== FUNÇÃO PRINCIPAL ===================
def main(single_run=True):
    """Função principal com sistema de diagnóstico robusto"""
    global _rpa_running, _keep_awake_thread
    
    _rpa_running = True
    
    gui_log("🤖 RPA iniciado com sistema de diagnóstico avançado")
    gui_log("📁 Logs de diagnóstico serão salvos em: debug_logs/")
    gui_log("⚠️ FAILSAFE: mova o mouse para canto superior esquerdo para parar")
    
    # Iniciar keep-awake
    _keep_awake_stop.clear()
    _keep_awake_thread = threading.Thread(
        target=keep_awake_loop,
        args=(_keep_awake_stop,),
        daemon=True
    )
    _keep_awake_thread.start()
    
    ciclo = 0
    tentativas_falhas = 0
    max_tentativas_falhas = 3
    
    try:
        while _rpa_running:
            ciclo += 1
            gui_log(f"\n{'='*60}")
            gui_log(f"🔄 CICLO #{ciclo}")
            gui_log(f"{'='*60}\n")
            
            sucesso = run_once()
            
            if sucesso:
                gui_log("✅ Ciclo concluído com sucesso!")
                tentativas_falhas = 0  # Reset contador
                
                if single_run:
                    gui_log("🎉 Execução única finalizada com sucesso")
                    break
            else:
                tentativas_falhas += 1
                gui_log(f"❌ Ciclo falhou ({tentativas_falhas}/{max_tentativas_falhas})")
                
                if tentativas_falhas >= max_tentativas_falhas:
                    gui_log("❌ Muitas falhas consecutivas, encerrando...")
                    break
                
                if single_run:
                    gui_log("⚠️ Modo single run - encerrando após falha")
                    break
                
                # Aguardar antes de tentar novamente
                wait_time = min(30 * tentativas_falhas, 120)
                gui_log(f"⏳ Aguardando {wait_time}s antes de tentar novamente...")
                time.sleep(wait_time)
            
            if _rpa_running and not single_run:
                time.sleep(5)
                
    except KeyboardInterrupt:
        gui_log("🛑 Interrompido pelo usuário")
    except pag.FailSafeException:
        gui_log("🛑 FAILSAFE acionado")
    except Exception as e:
        gui_log(f"❌ Erro inesperado: {e}")
        import traceback
        gui_log(traceback.format_exc())
    finally:
        _rpa_running = False
        _keep_awake_stop.set()
        
        gui_log("\n" + "="*60)
        gui_log("🏁 RPA FINALIZADO")
        gui_log("📊 Verifique a pasta 'debug_logs' para análise detalhada")
        gui_log("="*60)

if __name__ == "__main__":
    # Criar instância de diagnóstico para teste standalone
    _diagnostic = OracleDiagnostic(log_callback=print)
    main()