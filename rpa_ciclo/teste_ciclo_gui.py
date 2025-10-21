# -*- coding: utf-8 -*-
"""
TESTE COMPLETO DO RPA CICLO V2 - COM INTERFACE GRÁFICA
Interface moderna com logs em tempo real e controles
"""

import json
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk

# Configurar encoding UTF-8
if sys.platform.startswith('win'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

# =================== CONFIGURAÇÕES DE TESTE ===================
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"

# ─── MODO TESTE ATIVADO ─────────────────────────────────────────────
MODO_TESTE = True
SIMULAR_CLIQUES = True
LIMITE_ITENS_TESTE = 50
TESTAR_DUPLICACAO = True

# IDs das planilhas de TESTE
SPREADSHEET_ID_ORACLE_TESTE = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SPREADSHEET_ID_BANCADA_TESTE = "1KMS-1_FY6-cU26ZlaFu5jciSHEWlmluHo-QOFbB1LFE"

# Controle de execução
_rpa_running = False
_ciclo_atual = 0
_primeira_verificacao_oracle = True
_ja_processou_algum_item = False
_itens_processados_total = 0
_tentativas_duplicacao = 0
_duplicacoes_bloqueadas = 0

# ─── RATE LIMITING GOOGLE SHEETS API ───────────────────────────────
# Google Sheets API limita a 60 requisições de escrita por minuto
_ultima_requisicao_sheets = 0
_requisicoes_por_minuto = []

def rate_limit_sheets():
    """Garante que não excedemos 60 requisições por minuto"""
    global _ultima_requisicao_sheets, _requisicoes_por_minuto

    agora = time.time()

    # Remove requisições mais antigas que 1 minuto
    _requisicoes_por_minuto = [t for t in _requisicoes_por_minuto if agora - t < 60]

    # Se já temos 50+ requisições no último minuto, espera
    if len(_requisicoes_por_minuto) >= 50:  # Margem de segurança (50 em vez de 60)
        tempo_espera = 60 - (agora - _requisicoes_por_minuto[0])
        if tempo_espera > 0:
            print(f"⏳ Rate limit: Aguardando {tempo_espera:.1f}s...")
            time.sleep(tempo_espera + 1)

    # Registra esta requisição
    _requisicoes_por_minuto.append(time.time())

# =================== SIMULAÇÃO DE PYAUTOGUI ===================
class PyAutoGUISimulado:
    """Simula pyautogui para testes sem GUI real"""

    PAUSE = 0.1
    FAILSAFE = True

    @staticmethod
    def moveTo(x, y, duration=0.8):
        time.sleep(0.02)

    @staticmethod
    def click(button='left'):
        time.sleep(0.02)

    @staticmethod
    def doubleClick():
        time.sleep(0.02)

    @staticmethod
    def write(text):
        time.sleep(0.02)

    @staticmethod
    def press(key):
        time.sleep(0.02)

    @staticmethod
    def hotkey(*keys):
        time.sleep(0.02)

    class FailSafeException(Exception):
        pass

pyautogui = PyAutoGUISimulado()

# =================== GOOGLE SHEETS ===================
def autenticar_google_sheets():
    """Autentica com Google Sheets"""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    rpa_oracle_dir = BASE_DIR.parent / "rpa_oracle"
    token_path = rpa_oracle_dir / "token.json"
    creds_path = BASE_DIR / "CredenciaisOracle.json"

    if not creds_path.exists():
        creds_path = rpa_oracle_dir / "CredenciaisOracle.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("sheets", "v4", credentials=creds)

# =================== CACHE LOCAL ===================
class CacheLocal:
    """Cache persistente para evitar duplicações"""

    def __init__(self, arquivo="cache_teste_ciclo.json"):
        self.arquivo = BASE_DIR / arquivo
        self.dados = self._carregar()
        self.lock = threading.Lock()
        if not self.arquivo.exists() and not self.dados:
            self._salvar()

    def _carregar(self):
        if self.arquivo.exists():
            try:
                with open(self.arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _salvar(self):
        try:
            with open(self.arquivo, 'w', encoding='utf-8') as f:
                json.dump(self.dados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERRO] Falha ao salvar cache: {e}")

    def ja_processado(self, id_item):
        with self.lock:
            return id_item in self.dados

    def adicionar(self, id_item, linha_atual, item, quantidade, referencia, status="pendente"):
        if not id_item or str(id_item).strip() == "":
            return False

        dados_item = {
            "linha_atual": linha_atual,
            "item": item,
            "quantidade": quantidade,
            "referencia": referencia,
            "timestamp_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status_sheets": status
        }

        with self.lock:
            self.dados[id_item] = dados_item

        self._salvar()
        return True

    def marcar_concluido(self, id_item):
        removido = False
        with self.lock:
            if id_item in self.dados:
                del self.dados[id_item]
                removido = True

        if removido:
            self._salvar()

        return removido

    def get_pendentes(self):
        """Retorna lista de IDs pendentes (com status_sheets = 'pendente')"""
        with self.lock:
            return [id_item for id_item, dados in self.dados.items()
                    if dados.get("status_sheets") == "pendente"]

    def limpar(self):
        with self.lock:
            self.dados = {}
        self._salvar()

# =================== GUI PRINCIPAL ===================
class TesteRPACicloGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧪 Teste RPA Ciclo V2")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Variáveis
        self.service = None
        self.cache = None
        self.config = None
        self.thread_teste = None

        # Configurar estilo
        self.configurar_estilo()

        # Criar interface
        self.criar_interface()

    def configurar_estilo(self):
        """Configura estilo da interface"""
        style = ttk.Style()
        style.theme_use('clam')

        # Cores
        self.cor_primaria = "#2196F3"
        self.cor_sucesso = "#4CAF50"
        self.cor_erro = "#f44336"
        self.cor_aviso = "#FF9800"

    def criar_interface(self):
        """Cria todos os elementos da interface"""

        # ═══════════════════════════════════════════════════════════
        # FRAME SUPERIOR - Informações e Controles
        # ═══════════════════════════════════════════════════════════

        frame_top = tk.Frame(self.root, bg="#f5f5f5", relief=tk.RAISED, bd=2)
        frame_top.pack(fill=tk.X, padx=5, pady=5)

        # Título
        tk.Label(
            frame_top,
            text="🧪 TESTE COMPLETO DO RPA CICLO V2",
            font=("Arial", 16, "bold"),
            bg="#f5f5f5",
            fg="#333"
        ).pack(pady=10)

        # Frame de configurações
        config_frame = tk.LabelFrame(
            frame_top,
            text="⚙️ Configurações do Teste",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        config_frame.pack(padx=10, pady=5, fill=tk.X)

        # Grid de configs
        configs = [
            ("📦 Limite de Itens:", str(LIMITE_ITENS_TESTE)),
            ("🔄 Testar Duplicação:", "Sim" if TESTAR_DUPLICACAO else "Não"),
            ("🖱️ Simular Cliques:", "Sim" if SIMULAR_CLIQUES else "Não"),
        ]

        for i, (label, value) in enumerate(configs):
            tk.Label(
                config_frame,
                text=label,
                font=("Arial", 9),
                bg="#f5f5f5",
                anchor="w"
            ).grid(row=i, column=0, sticky="w", padx=10, pady=2)

            tk.Label(
                config_frame,
                text=value,
                font=("Arial", 9, "bold"),
                bg="#f5f5f5",
                fg=self.cor_primaria,
                anchor="w"
            ).grid(row=i, column=1, sticky="w", padx=10, pady=2)

        # ═══════════════════════════════════════════════════════════
        # FRAME ESTATÍSTICAS
        # ═══════════════════════════════════════════════════════════

        self.stats_frame = tk.LabelFrame(
            frame_top,
            text="📊 Estatísticas em Tempo Real",
            font=("Arial", 10, "bold"),
            bg="#f5f5f5",
            fg="#333"
        )
        self.stats_frame.pack(padx=10, pady=5, fill=tk.X)

        # Labels de estatísticas
        self.stats_labels = {}
        stats_config = [
            ("ciclos", "🔄 Ciclos:", "0"),
            ("itens", "📦 Itens Processados:", "0"),
            ("duplicacoes", "🛡️ Duplicações Bloqueadas:", "0/0"),
            ("taxa", "📈 Taxa de Bloqueio:", "0%"),
        ]

        for i, (key, label, default) in enumerate(stats_config):
            row = i // 2
            col = (i % 2) * 2

            tk.Label(
                self.stats_frame,
                text=label,
                font=("Arial", 9),
                bg="#f5f5f5",
                anchor="w"
            ).grid(row=row, column=col, sticky="w", padx=10, pady=2)

            value_label = tk.Label(
                self.stats_frame,
                text=default,
                font=("Arial", 9, "bold"),
                bg="#f5f5f5",
                fg=self.cor_sucesso,
                anchor="w"
            )
            value_label.grid(row=row, column=col + 1, sticky="w", padx=10, pady=2)
            self.stats_labels[key] = value_label

        # ═══════════════════════════════════════════════════════════
        # FRAME CONTROLES
        # ═══════════════════════════════════════════════════════════

        control_frame = tk.Frame(frame_top, bg="#f5f5f5")
        control_frame.pack(pady=10)

        # Botões
        self.btn_iniciar = tk.Button(
            control_frame,
            text="▶ Iniciar Teste",
            font=("Arial", 11, "bold"),
            bg=self.cor_sucesso,
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            command=self.iniciar_teste,
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_parar = tk.Button(
            control_frame,
            text="⏸ Parar Teste",
            font=("Arial", 11, "bold"),
            bg=self.cor_erro,
            fg="white",
            activebackground="#d32f2f",
            activeforeground="white",
            command=self.parar_teste,
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3,
            state=tk.DISABLED
        )
        self.btn_parar.pack(side=tk.LEFT, padx=5)

        self.btn_limpar_cache = tk.Button(
            control_frame,
            text="🗑️ Limpar Cache",
            font=("Arial", 11, "bold"),
            bg=self.cor_aviso,
            fg="white",
            activebackground="#f57c00",
            activeforeground="white",
            command=self.limpar_cache,
            width=15,
            height=2,
            relief=tk.RAISED,
            bd=3
        )
        self.btn_limpar_cache.pack(side=tk.LEFT, padx=5)

        # ═══════════════════════════════════════════════════════════
        # FRAME LOGS
        # ═══════════════════════════════════════════════════════════

        log_frame = tk.LabelFrame(
            self.root,
            text="📋 Logs em Tempo Real",
            font=("Arial", 10, "bold"),
            bg="#fff",
            fg="#333"
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Área de texto com scroll
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.SUNKEN,
            bd=2
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Configurar tags de cores
        self.log_text.tag_config("info", foreground="#4fc3f7")
        self.log_text.tag_config("sucesso", foreground="#81c784")
        self.log_text.tag_config("erro", foreground="#e57373")
        self.log_text.tag_config("aviso", foreground="#ffb74d")
        self.log_text.tag_config("importante", foreground="#ba68c8", font=("Consolas", 9, "bold"))

        # ═══════════════════════════════════════════════════════════
        # BARRA DE STATUS
        # ═══════════════════════════════════════════════════════════

        self.status_bar = tk.Label(
            self.root,
            text="⏸ Aguardando início do teste...",
            font=("Arial", 9),
            bg="#333",
            fg="white",
            anchor="w",
            relief=tk.SUNKEN
        )
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Log inicial
        self.log("🚀 Interface carregada com sucesso!", "sucesso")
        self.log("📌 Configure as opções e clique em 'Iniciar Teste'", "info")

    def log(self, msg, tipo="info"):
        """Adiciona mensagem ao log com timestamp e cor"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n", tipo)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def atualizar_stats(self):
        """Atualiza estatísticas na interface"""
        self.stats_labels["ciclos"].config(text=str(_ciclo_atual))
        self.stats_labels["itens"].config(text=str(_itens_processados_total))
        self.stats_labels["duplicacoes"].config(text=f"{_duplicacoes_bloqueadas}/{_tentativas_duplicacao}")

        if _tentativas_duplicacao > 0:
            taxa = (_duplicacoes_bloqueadas / _tentativas_duplicacao) * 100
            cor = self.cor_sucesso if taxa == 100 else self.cor_aviso
            self.stats_labels["taxa"].config(text=f"{taxa:.1f}%", fg=cor)

    def iniciar_teste(self):
        """Inicia o teste em thread separada"""
        global _rpa_running

        if _rpa_running:
            messagebox.showwarning("Teste em Andamento", "O teste já está em execução!")
            return

        # Confirmar início
        resposta = messagebox.askyesno(
            "Iniciar Teste",
            "Deseja iniciar o teste completo do RPA Ciclo V2?\n\n"
            "O teste irá:\n"
            "• Processar até 50 itens por ciclo\n"
            "• Testar anti-duplicação\n"
            "• Simular todos os cliques\n"
            "• Executar 3 ciclos completos\n\n"
            "Continuar?"
        )

        if not resposta:
            return

        # Perguntar sobre cache
        if Path(BASE_DIR / "cache_teste_ciclo.json").exists():
            num_itens = len(self.cache.dados) if self.cache else 0
            limpar = messagebox.askyesno(
                "Limpar Cache",
                f"⚠️ ATENÇÃO: Cache existente com {num_itens} itens.\n\n"
                f"O cache protege contra duplicações.\n"
                f"Items só devem ser removidos após sucesso no Google Sheets.\n\n"
                f"Deseja limpar o cache agora?\n\n"
                f"✅ NÃO (Recomendado) = Mantém cache e proteção\n"
                f"⚠️ SIM = Limpa cache (apenas para testes do zero)"
            )

            if limpar:
                if self.cache:
                    self.cache.limpar()
                    self.log("🗑️ Cache limpo com sucesso!", "aviso")
                    self.log("⚠️ Proteção contra duplicação resetada", "aviso")
            else:
                self.log(f"💾 Cache mantido: {num_itens} itens protegidos", "sucesso")

        # Atualizar UI
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_parar.config(state=tk.NORMAL)
        self.btn_limpar_cache.config(state=tk.DISABLED)
        self.status_bar.config(text="▶ Teste em execução...", bg=self.cor_sucesso)

        # Iniciar thread
        self.thread_teste = threading.Thread(target=self.executar_teste_completo, daemon=True)
        self.thread_teste.start()

    def parar_teste(self):
        """Para o teste"""
        global _rpa_running

        resposta = messagebox.askyesno(
            "Parar Teste",
            "Deseja realmente parar o teste?\n\n"
            "O teste será interrompido e as estatísticas finais serão exibidas."
        )

        if resposta:
            _rpa_running = False
            self.log("⏸ Parando teste...", "aviso")
            self.status_bar.config(text="⏸ Parando teste...", bg=self.cor_aviso)

    def limpar_cache(self):
        """Limpa o cache"""
        resposta = messagebox.askyesno(
            "Limpar Cache",
            "Deseja limpar o cache de teste?\n\n"
            "Isso removerá todos os itens processados do cache."
        )

        if resposta:
            if not self.cache:
                self.cache = CacheLocal("cache_teste_ciclo.json")

            self.cache.limpar()
            self.log("🗑️ Cache limpo com sucesso!", "sucesso")
            messagebox.showinfo("Cache Limpo", "Cache limpo com sucesso!")

    def executar_teste_completo(self):
        """Executa o teste completo (roda em thread separada)"""
        global _rpa_running, _ciclo_atual, _primeira_verificacao_oracle
        global _itens_processados_total, _tentativas_duplicacao, _duplicacoes_bloqueadas
        global _ja_processou_algum_item

        _rpa_running = True

        try:
            # Autenticar
            self.log("🔐 Autenticando Google Sheets...", "info")
            self.service = autenticar_google_sheets()
            self.log("✅ Autenticado com sucesso!", "sucesso")

            # Carregar config
            self.log("⚙️ Carregando configurações...", "info")
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            self.log("✅ Configurações carregadas!", "sucesso")

            # Inicializar cache
            self.cache = CacheLocal("cache_teste_ciclo.json")
            self.log(f"💾 Cache carregado: {len(self.cache.dados)} itens", "info")

            # Executar ciclos
            NUM_CICLOS = 3

            for ciclo_num in range(1, NUM_CICLOS + 1):
                if not _rpa_running:
                    break

                _ciclo_atual = ciclo_num
                _primeira_verificacao_oracle = True

                self.log("=" * 70, "importante")
                self.log(f"🔄 CICLO #{ciclo_num}/{NUM_CICLOS} - {datetime.now().strftime('%H:%M:%S')}", "importante")
                self.log("=" * 70, "importante")

                # Executar etapas
                sucesso = self.executar_ciclo()

                # Atualizar stats
                self.root.after(0, self.atualizar_stats)

                if sucesso:
                    self.log(f"✅ CICLO #{ciclo_num} CONCLUÍDO COM SUCESSO!", "sucesso")

                    if ciclo_num < NUM_CICLOS:
                        self.log("⏳ Aguardando 2s antes do próximo ciclo...", "info")
                        time.sleep(2)
                else:
                    self.log(f"❌ CICLO #{ciclo_num} FALHOU!", "erro")
                    break

            # Estatísticas finais
            self.exibir_estatisticas_finais()

        except Exception as e:
            self.log(f"❌ Erro fatal: {e}", "erro")
            import traceback
            self.log(traceback.format_exc(), "erro")
        finally:
            _rpa_running = False
            self.root.after(0, self.finalizar_teste)

    def executar_ciclo(self):
        """Executa um ciclo completo"""
        # Importar função de processamento
        from teste_ciclo_completo import (
            etapa_01_transferencia_subinventario,
            etapa_02_preencher_tipo,
            etapa_03_selecionar_funcionario,
            etapa_06_navegacao_pos_oracle,
            etapa_07_bancada_material,
            etapa_08_executar_rpa_bancada_teste,
            etapa_09_fechar_bancada
        )

        # Adaptar gui_log para usar self.log
        import teste_ciclo_completo
        teste_ciclo_completo.gui_log = lambda msg: self.log(msg, "info")

        etapas = [
            ("Transferência Subinventário", etapa_01_transferencia_subinventario),
            ("Preenchimento Tipo", etapa_02_preencher_tipo),
            ("Seleção Funcionário", etapa_03_selecionar_funcionario),
            ("RPA Oracle", lambda c: self.executar_oracle_teste()),
            ("Navegação", etapa_06_navegacao_pos_oracle),
            ("Bancada Material", etapa_07_bancada_material),
            ("RPA Bancada", lambda c: etapa_08_executar_rpa_bancada_teste()),
            ("Fechamento", etapa_09_fechar_bancada)
        ]

        for nome, funcao in etapas:
            if not _rpa_running:
                return False

            sucesso = funcao(self.config)

            if not sucesso:
                self.log(f"❌ Falha na etapa: {nome}", "erro")
                return False

        return True

    def sync_sheets_background_gui(self):
        """Thread que tenta atualizar Sheets para linhas pendentes (com rate limiting)"""
        SHEET_NAME = "Separação"
        ciclo_retry = 0
        MAX_ITENS_POR_BATCH = 10  # Processar no máximo 10 itens por vez

        while _rpa_running:
            time.sleep(30)  # Retry a cada 30 segundos

            try:
                ciclo_retry += 1
                pendentes = self.cache.get_pendentes()

                if not pendentes:
                    continue

                # Limitar a 10 itens por vez
                pendentes = pendentes[:MAX_ITENS_POR_BATCH]
                self.log(f"[RETRY] Ciclo {ciclo_retry} - Processando {len(pendentes)} itens pendentes...", "aviso")

                # Buscar headers do Sheets
                rate_limit_sheets()  # Aplicar rate limiting
                res = self.service.spreadsheets().values().get(
                    spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                    range=f"{SHEET_NAME}!A1:AC"
                ).execute()

                valores = res.get("values", [])
                if not valores:
                    continue

                headers = valores[0]
                idx_status_oracle = headers.index("Status Oracle")
                coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)

                # Coletar atualizações para batch update
                batch_updates = []
                ids_para_remover = []

                for id_item in pendentes:
                    dados_cache = self.cache.dados.get(id_item, {})
                    linha_atual = dados_cache.get("linha_atual")

                    if linha_atual:
                        batch_updates.append({
                            "range": f"{SHEET_NAME}!{coluna_letra}{linha_atual}",
                            "values": [["Processo Oracle Concluído"]]
                        })
                        ids_para_remover.append(id_item)

                # Executar batch update se tiver algo
                if batch_updates:
                    try:
                        rate_limit_sheets()  # Aplicar rate limiting
                        self.service.spreadsheets().values().batchUpdate(
                            spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                            body={"valueInputOption": "RAW", "data": batch_updates}
                        ).execute()

                        # SUCESSO! Remover do cache
                        for id_item in ids_para_remover:
                            self.cache.marcar_concluido(id_item)

                        self.log(f"[RETRY] ✓ {len(ids_para_remover)} itens sincronizados e removidos do cache", "sucesso")
                        self.root.after(0, self.atualizar_stats)

                    except Exception as e:
                        self.log(f"[RETRY] ✗ Batch update falhou: {str(e)[:100]}", "erro")

            except Exception as e:
                self.log(f"[RETRY] Erro no ciclo {ciclo_retry}: {str(e)[:100]}", "erro")

    def executar_oracle_teste(self):
        """Executa processamento Oracle de teste"""
        global _primeira_verificacao_oracle, _ja_processou_algum_item
        global _itens_processados_total, _tentativas_duplicacao, _duplicacoes_bloqueadas

        self.log("🤖 ETAPA: Processamento no Oracle (TESTE)", "importante")

        SHEET_NAME = "Separação"

        # Iniciar thread de retry em background (apenas uma vez)
        if not hasattr(self, '_retry_thread_started'):
            retry_thread = threading.Thread(target=self.sync_sheets_background_gui, daemon=True)
            retry_thread.start()
            self._retry_thread_started = True
            self.log("[RETRY] Thread de retry automático iniciada", "info")

        # Buscar dados
        res = self.service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
            range=f"{SHEET_NAME}!A1:AC"
        ).execute()

        valores = res.get("values", [])
        if not valores:
            self.log("⚠️ Planilha vazia!", "aviso")
            return True

        headers, dados = valores[0], valores[1:]
        self.log(f"📊 {len(dados)} linhas encontradas", "info")

        # Filtrar linhas
        linhas = []
        for i, row in enumerate(dados):
            if len(row) < len(headers):
                row += [''] * (len(headers) - len(row))

            try:
                idx_status_oracle = headers.index("Status Oracle")
                idx_status = headers.index("Status")
                idx_id = headers.index("ID")
            except ValueError:
                continue

            status_oracle = row[idx_status_oracle].strip() if idx_status_oracle < len(row) else ""
            status = row[idx_status].strip().upper() if idx_status < len(row) else ""

            if status_oracle == "" and "CONCLUÍDO" in status:
                linhas.append((i + 2, dict(zip(headers, row))))

        # Limitar
        if len(linhas) > LIMITE_ITENS_TESTE:
            linhas = linhas[:LIMITE_ITENS_TESTE]

        self.log(f"📋 {len(linhas)} linhas para processar", "info")

        # Processar
        itens_processados = 0
        ids_processados = []  # Lista de IDs processados neste ciclo
        batch_updates = []  # Coletar atualizações para batch update
        ids_para_atualizar = []  # IDs correspondentes ao batch

        for idx, (i, linha) in enumerate(linhas, 1):
            if not _rpa_running:
                return False

            id_item = linha.get("ID", "").strip()
            if not id_item:
                continue

            # ═══════════════════════════════════════════════════════════════
            # TESTE DE DUPLICAÇÃO - Tentar processar item já processado
            # ═══════════════════════════════════════════════════════════════
            if TESTAR_DUPLICACAO and idx % 5 == 0 and len(ids_processados) > 0:
                _tentativas_duplicacao += 1
                # Pegar um ID já processado para tentar duplicar
                id_duplicado = ids_processados[0]  # Pega o primeiro processado
                self.log(f"🔄 [TESTE DUPLICAÇÃO #{_tentativas_duplicacao}] Tentando duplicar ID {id_duplicado}...", "aviso")

                # Tentar processar novamente (deve ser bloqueado)
                if self.cache.ja_processado(id_duplicado):
                    _duplicacoes_bloqueadas += 1
                    self.log(f"🛡️ [BLOQUEADO] ID {id_duplicado} já foi processado! ({_duplicacoes_bloqueadas}/{_tentativas_duplicacao})", "sucesso")
                    self.root.after(0, self.atualizar_stats)
                else:
                    self.log(f"⚠️ [FALHA CACHE] ID {id_duplicado} NÃO estava no cache!", "erro")

            # Verificar se o item atual já foi processado (não deveria)
            if self.cache.ja_processado(id_item):
                self.log(f"⏭️ [PULADO] ID {id_item} já processado anteriormente", "aviso")
                continue

            item = linha.get("Item", "")
            quantidade = linha.get("Quantidade", "")

            self.log(f"▶ ({idx}/{len(linhas)}) ID={id_item} | Item={item} | Qtd={quantidade}", "info")
            time.sleep(0.05)

            # Adicionar ao cache
            self.cache.adicionar(id_item, i, item, quantidade, "", "pendente")

            # ═══════════════════════════════════════════════════════════════
            # COLETAR PARA BATCH UPDATE (em vez de atualizar individualmente)
            # ═══════════════════════════════════════════════════════════════
            # Calcular letra da coluna Status Oracle
            idx_status_oracle = headers.index("Status Oracle")
            coluna_letra = chr(65 + idx_status_oracle) if idx_status_oracle < 26 else chr(65 + idx_status_oracle // 26 - 1) + chr(65 + idx_status_oracle % 26)

            batch_updates.append({
                "range": f"{SHEET_NAME}!{coluna_letra}{i}",
                "values": [["Processo Oracle Concluído"]]
            })
            ids_para_atualizar.append((id_item, i))

            self.log(f"  [PREPARADO] Atualização da linha {i} adicionada ao batch", "info")

            # Guardar para teste de duplicação
            ids_processados.append(id_item)

            itens_processados += 1
            _itens_processados_total += 1
            _ja_processou_algum_item = True

            self.root.after(0, self.atualizar_stats)

        # ═══════════════════════════════════════════════════════════════
        # EXECUTAR BATCH UPDATE (uma única requisição para todos os itens)
        # ═══════════════════════════════════════════════════════════════
        if batch_updates:
            self.log(f"", "info")
            self.log(f"📤 Executando batch update: {len(batch_updates)} linha(s) para atualizar...", "info")

            try:
                # Aplicar rate limiting
                rate_limit_sheets()

                # Executar batch update
                self.service.spreadsheets().values().batchUpdate(
                    spreadsheetId=SPREADSHEET_ID_ORACLE_TESTE,
                    body={"valueInputOption": "RAW", "data": batch_updates}
                ).execute()

                self.log(f"✅ Batch update concluído! {len(batch_updates)} linhas atualizadas no Sheets!", "sucesso")

                # SUCESSO! Remover todos os IDs do cache
                for id_item, linha_num in ids_para_atualizar:
                    if self.cache.marcar_concluido(id_item):
                        self.log(f"💾 ID {id_item} (linha {linha_num}) removido do cache (sincronizado)", "sucesso")

            except Exception as err_batch:
                self.log(f"❌ Erro no batch update: {err_batch}", "erro")
                self.log(f"💾 {len(ids_para_atualizar)} IDs permanecem no cache. Thread de retry tentará novamente...", "aviso")
                # Items ficam no cache como "pendente" para retry

        self.log(f"✅ {itens_processados} itens processados", "sucesso")
        return True

    def exibir_estatisticas_finais(self):
        """Exibe estatísticas finais do teste"""
        self.log("=" * 70, "importante")
        self.log("📊 ESTATÍSTICAS FINAIS DO TESTE", "importante")
        self.log("=" * 70, "importante")
        self.log(f"✅ Ciclos executados: {_ciclo_atual}", "sucesso")
        self.log(f"📦 Total de itens processados: {_itens_processados_total}", "info")
        self.log(f"🔄 Tentativas de duplicação: {_tentativas_duplicacao}", "info")
        self.log(f"🛡️ Duplicações bloqueadas: {_duplicacoes_bloqueadas}", "sucesso")

        if _tentativas_duplicacao > 0:
            taxa = (_duplicacoes_bloqueadas / _tentativas_duplicacao) * 100
            cor = "sucesso" if taxa == 100 else "aviso"
            self.log(f"📈 Taxa de bloqueio: {taxa:.1f}%", cor)

        self.log("=" * 70, "importante")

        # Salvar relatório
        relatorio = {
            "data_teste": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ciclos_executados": _ciclo_atual,
            "itens_processados": _itens_processados_total,
            "tentativas_duplicacao": _tentativas_duplicacao,
            "duplicacoes_bloqueadas": _duplicacoes_bloqueadas,
            "configuracoes": {
                "limite_itens": LIMITE_ITENS_TESTE,
                "testar_duplicacao": TESTAR_DUPLICACAO
            }
        }

        relatorio_path = BASE_DIR / "relatorio_teste_ciclo_gui.json"
        with open(relatorio_path, 'w', encoding='utf-8') as f:
            json.dump(relatorio, f, indent=2, ensure_ascii=False)

        self.log(f"📄 Relatório salvo: {relatorio_path.name}", "sucesso")

    def finalizar_teste(self):
        """Finaliza o teste e restaura UI"""
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_parar.config(state=tk.DISABLED)
        self.btn_limpar_cache.config(state=tk.NORMAL)
        self.status_bar.config(text="⏸ Teste finalizado", bg="#333")

        messagebox.showinfo(
            "Teste Concluído",
            f"Teste finalizado!\n\n"
            f"Ciclos: {_ciclo_atual}\n"
            f"Itens: {_itens_processados_total}\n"
            f"Duplicações bloqueadas: {_duplicacoes_bloqueadas}/{_tentativas_duplicacao}\n\n"
            f"Verifique o relatório: relatorio_teste_ciclo_gui.json"
        )

# =================== MAIN ===================
def main():
    """Função principal"""
    root = tk.Tk()
    app = TesteRPACicloGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
