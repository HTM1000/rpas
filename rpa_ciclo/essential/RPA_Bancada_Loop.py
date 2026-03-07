#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA BANCADA LOOP - Extração contínua da Bancada de Material
Executa em loop infinito:
1. Navega até Bancada de Material
2. Extrai dados (Detalhado + Copiar)
3. Salva Excel local + Google Sheets
4. Fecha a bancada
5. Repete (SEM DORMIR - proteção anti-hibernação)
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import pyautogui
import pyperclip
import keyboard

# Proteção contra hibernação/screensaver
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.1

# =================== VARIÁVEIS GLOBAIS ===================
_rpa_running = False
_ciclo_numero = 0
_gui_log_widget = None

# =================== REDIRECIONADOR DE STDOUT ===================
class StdoutRedirector:
    """Redireciona print() para a GUI"""
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        if text.strip():  # Ignora linhas vazias
            try:
                self.widget.config(state='normal')
                self.widget.insert('end', f"{text}\n")
                self.widget.see('end')
                self.widget.config(state='disabled')
                self.widget.update_idletasks()
            except:
                pass

    def flush(self):
        pass

# =================== CARREGAR CONFIGURAÇÕES ===================
def carregar_config():
    """Carrega config.json"""
    config_path = Path(__file__).parent / "config.json"

    if not config_path.exists():
        print(f"ERRO: config.json não encontrado em {config_path}")
        return None

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = carregar_config()
if not CONFIG:
    print("ERRO CRÍTICO: Não foi possível carregar configurações!")
    sys.exit(1)

# =================== FUNÇÕES DE LOG ===================
def gui_log(mensagem):
    """Adiciona mensagem ao log da GUI"""
    global _gui_log_widget

    timestamp = datetime.now().strftime("%H:%M:%S")
    msg_completa = f"[{timestamp}] {mensagem}"

    print(msg_completa)

    if _gui_log_widget:
        try:
            _gui_log_widget.insert(tk.END, msg_completa + "\n")
            _gui_log_widget.see(tk.END)
        except:
            pass

# =================== FUNÇÕES DE CLIQUE ===================
def clicar_coordenada(x, y, duplo=False, descricao=""):
    """Clica em uma coordenada"""
    global _rpa_running

    if not _rpa_running:
        return False

    try:
        if duplo:
            gui_log(f">> Duplo clique em ({x}, {y}) - {descricao}")
            pyautogui.doubleClick(x, y)
        else:
            gui_log(f">> Clique em ({x}, {y}) - {descricao}")
            pyautogui.click(x, y)
        return True
    except Exception as e:
        gui_log(f"ERRO ao clicar: {e}")
        return False

def aguardar_com_pausa(segundos, mensagem="Aguardando", evitar_hibernar=False):
    """Aguarda X segundos com verificação de _rpa_running"""
    global _rpa_running

    gui_log(f"⏳ {mensagem} ({segundos}s)...")

    inicio = time.time()

    while time.time() - inicio < segundos:
        if not _rpa_running:
            gui_log(f"⚠️ Aguardar interrompido ({mensagem})")
            return False

        # Anti-hibernação durante espera
        if evitar_hibernar and int(time.time() - inicio) % 10 == 0:
            try:
                pyautogui.move(1, 0)
                time.sleep(0.05)
                pyautogui.move(-1, 0)
            except:
                pass

        time.sleep(0.5)

    return True

# =================== SISTEMA ANTI-HIBERNAÇÃO ===================
def iniciar_movimento_mouse_continuo():
    """Inicia thread que move mouse continuamente (anti-hibernação ULTRA)"""
    stop_event = threading.Event()

    def mover_mouse_loop():
        gui_log("🖱️ Thread anti-hibernação INICIADA")
        contador_shift = 0

        while not stop_event.is_set() and _rpa_running:
            try:
                # Mover mouse 5px
                pyautogui.move(5, 0)
                time.sleep(0.05)
                pyautogui.move(-5, 0)

                # Pressionar Shift a cada 15 segundos
                contador_shift += 1
                if contador_shift >= 30:  # 30 * 0.5s = 15s
                    pyautogui.press('shift')
                    contador_shift = 0

            except:
                pass

            time.sleep(1)

        gui_log("🖱️ Thread anti-hibernação PARADA")

    thread = threading.Thread(target=mover_mouse_loop, daemon=True)
    thread.start()

    return stop_event

# =================== MONITORAMENTO DE CLIPBOARD ===================
def monitorar_clipboard_inteligente(max_tempo=900, intervalo_check=3, estabilidade_segundos=30):
    """
    Monitora clipboard até dados serem copiados completamente
    Retorna o texto copiado quando clipboard estabilizar
    """
    global _rpa_running

    gui_log(f"📋 Monitorando clipboard (máx: {max_tempo//60}min, check: {intervalo_check}s)")

    inicio = time.time()
    ultimo_tamanho = 0
    tempo_estavel = None
    tentativa = 0

    while time.time() - inicio < max_tempo:
        if not _rpa_running:
            gui_log("⚠️ Monitoramento interrompido")
            return None

        tentativa += 1

        try:
            texto_atual = pyperclip.paste()
            tamanho_atual = len(texto_atual) if texto_atual else 0

            # Clipboard mudou?
            if tamanho_atual != ultimo_tamanho:
                if tamanho_atual > 50:  # Tem dados válidos
                    gui_log(f"📊 Clipboard mudou: {tamanho_atual:,} chars (+{tamanho_atual - ultimo_tamanho:,})")
                    tempo_estavel = time.time()
                ultimo_tamanho = tamanho_atual

            # Clipboard estável há X segundos?
            if tempo_estavel and tamanho_atual > 50:
                tempo_desde_mudanca = time.time() - tempo_estavel

                if tempo_desde_mudanca >= estabilidade_segundos:
                    gui_log(f"✅ Clipboard estável por {estabilidade_segundos}s - CÓPIA COMPLETA!")
                    gui_log(f"📦 Total copiado: {tamanho_atual:,} caracteres")
                    return texto_atual

                # Mostrar progresso
                if int(tempo_desde_mudanca) % 5 == 0:
                    gui_log(f"⏳ Aguardando estabilidade... ({int(tempo_desde_mudanca)}s/{estabilidade_segundos}s)")

        except Exception as e:
            gui_log(f"⚠️ Erro ao monitorar clipboard: {e}")

        time.sleep(intervalo_check)

    # Timeout
    gui_log(f"⏱️ TIMEOUT após {max_tempo//60} minutos")
    if ultimo_tamanho > 50:
        gui_log(f"⚠️ Retornando dados parciais: {ultimo_tamanho:,} chars")
        return pyperclip.paste()

    return None

# =================== PROCESSAR DADOS DA BANCADA ===================
def processar_dados_bancada(texto_copiado):
    """Processa texto TSV copiado da bancada"""
    try:
        import pandas as pd

        if not texto_copiado or len(texto_copiado) < 50:
            gui_log("❌ Texto vazio ou muito curto")
            return None

        # Converter TSV para DataFrame
        from io import StringIO
        df = pd.read_csv(StringIO(texto_copiado), sep='\t', dtype=str)

        gui_log(f"✅ DataFrame criado: {len(df):,} linhas x {len(df.columns)} colunas")

        return df

    except Exception as e:
        gui_log(f"❌ Erro ao processar dados: {e}")
        import traceback
        gui_log(traceback.format_exc())
        return None

def salvar_excel_bancada(df):
    """Salva DataFrame em Excel"""
    try:
        # Criar pasta de saída
        base_dir = Path(__file__).parent
        out_dir = base_dir / "rpa_bancada" / "out"
        out_dir.mkdir(parents=True, exist_ok=True)

        # Nome do arquivo
        hoje = datetime.now().strftime("%Y-%m-%d")
        arquivo = out_dir / f"bancada-{hoje}.xlsx"

        # Salvar
        df.to_excel(arquivo, index=False, engine='openpyxl')

        gui_log(f"💾 Excel salvo: {arquivo.name}")
        return str(arquivo)

    except Exception as e:
        gui_log(f"❌ Erro ao salvar Excel: {e}")
        return None

def enviar_google_sheets(df):
    """Envia dados para Google Sheets (bancada)"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from google_sheets_manager import enviar_para_google_sheets

        gui_log("   ☁️  Enviando para Google Sheets...")
        sucesso = enviar_para_google_sheets(df)

        if sucesso:
            gui_log("   ✅  Google Sheets atualizado!")
        else:
            gui_log("   ⚠️  Falha ao enviar Sheets")

        return sucesso

    except Exception as e:
        gui_log(f"   ❌ Erro Sheets: {e}")
        return False

# =================== ETAPAS DO CICLO DA BANCADA ===================
def abrir_bancada():
    """Navega até o menu e abre a Bancada de Material"""
    global _rpa_running

    tempo_espera = CONFIG["tempos_espera"]["entre_cliques"]

    # 1. Clicar em "Janela" para dar foco
    gui_log("   🖱️  [1/3] Clicando em 'Janela'...")
    coord = CONFIG["coordenadas"]["navegador_janela"]
    if not clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"]):
        return False
    if not aguardar_com_pausa(tempo_espera, ""):
        return False

    # 2. Clicar no menu de navegação
    gui_log("   🖱️  [2/3] Clicando no 'Menu de Navegação'...")
    coord = CONFIG["coordenadas"]["navegador_menu"]
    if not clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"]):
        return False
    if not aguardar_com_pausa(tempo_espera, ""):
        return False

    # 3. Duplo clique em "Bancada de Material"
    gui_log("   📂  [3/3] Duplo clique em 'Bancada de Material'...")
    coord = CONFIG["coordenadas"]["tela_07_bancada_material"]
    if not clicar_coordenada(coord["x"], coord["y"], duplo=True, descricao=coord["descricao"]):
        return False

    tempo_espera_modal = CONFIG["tempos_espera"]["apos_modal"]
    if not aguardar_com_pausa(tempo_espera_modal, ""):
        return False

    gui_log("   ✅  Bancada aberta!")
    return True

def executar_bancada():
    """Extrai dados da Bancada"""
    global _rpa_running

    # 1. Clicar checkbox "Detalhado"
    gui_log("   ☑️  [1/7] Clicando checkbox 'Detalhado'...")
    coord = CONFIG["coordenadas"]["bancada_detalhado"]
    if not clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"]):
        return False
    time.sleep(2.0)
    if not _rpa_running:
        return False

    # 2. Enter para localizar
    gui_log("   ⌨️  [2/7] Enter (localizar itens)...")
    pyautogui.press('enter')
    time.sleep(1.2)
    if not _rpa_running:
        return False

    # 3. Aguardar 2 minutos (grid carregar)
    gui_log("   ⏳  [3/7] Aguardando 2 minutos (grid carregando)...")
    if not aguardar_com_pausa(120, "", evitar_hibernar=True):
        return False

    # 4. Clicar célula Org
    gui_log("   🖱️  [4/7] Clicando célula Org...")
    coord = CONFIG["coordenadas"]["bancada_celula_org"]
    if not clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"]):
        return False
    if not _rpa_running:
        return False

    # 5. Copiar dados (menu contexto)
    gui_log("   📋  [5/7] Abrindo menu contexto (Shift+F10)...")
    pyperclip.copy('')
    time.sleep(0.3)
    pyautogui.hotkey('shift', 'f10')
    time.sleep(1.5)

    for i in range(3):
        pyautogui.press('down')
        time.sleep(0.25)

    pyautogui.press('enter')
    time.sleep(0.6)
    if not _rpa_running:
        return False

    # 6. Monitorar clipboard
    gui_log("   ⏳  [6/7] Monitorando clipboard (aguardando dados)...")
    stop_mouse_event = iniciar_movimento_mouse_continuo()

    texto_copiado = monitorar_clipboard_inteligente(
        max_tempo=15 * 60,
        intervalo_check=3,
        estabilidade_segundos=30
    )

    try:
        stop_mouse_event.set()
    except:
        pass

    if not texto_copiado or len(texto_copiado) < 50:
        gui_log("")
        gui_log("   ❌ Clipboard vazio!")
        return False

    linhas = texto_copiado.count('\n')
    gui_log(f"   ✅  Dados copiados: {linhas:,} linhas")

    # 7. Processar e salvar
    gui_log("   💾  [7/7] Processando e salvando dados...")
    df = processar_dados_bancada(texto_copiado)

    if df is None or df.empty:
        gui_log("   ❌ Falha ao processar!")
        return False

    gui_log(f"   ✅  Processado: {len(df):,} linhas x {len(df.columns)} colunas")

    # Salvar Excel local
    arquivo_excel = salvar_excel_bancada(df)
    if arquivo_excel:
        gui_log(f"   💾  Excel salvo: {os.path.basename(arquivo_excel)}")

    # Enviar Google Sheets
    enviar_google_sheets(df)

    gui_log("   ✅  Extração concluída!")
    return True

def fechar_bancada():
    """Fecha a janela da Bancada"""
    global _rpa_running

    gui_log("   🔴  Fechando janela da Bancada...")
    coord = CONFIG["coordenadas"]["tela_08_fechar_bancada"]
    if not clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"]):
        return False

    tempo_espera = CONFIG["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, ""):
        return False

    gui_log("   ✅  Bancada fechada!")
    return True

# =================== LOOP PRINCIPAL ===================
def executar_loop_bancada():
    """Loop infinito da bancada"""
    global _rpa_running, _ciclo_numero

    gui_log("")
    gui_log("=" * 70)
    gui_log("🔄 INICIANDO LOOP INFINITO DA BANCADA")
    gui_log("=" * 70)
    gui_log("⚠️ Pressione ESC a qualquer momento para parar")
    gui_log("")

    # AUTENTICAR GOOGLE SHEETS LOGO NO INÍCIO
    gui_log("=" * 70)
    gui_log("🔐 PASSO 1: AUTENTICANDO GOOGLE SHEETS")
    gui_log("=" * 70)
    gui_log("")

    try:
        gui_log("[1/5] Inserindo path do módulo...")
        sys.path.insert(0, str(Path(__file__).parent))
        gui_log("      ✅ Path inserido")

        gui_log("[2/5] Importando google_sheets_manager...")
        from google_sheets_manager import get_sheets_service
        gui_log("      ✅ Módulo importado")

        gui_log("[3/5] Verificando se token.json existe...")
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        token_path = os.path.join(data_path, 'token.json')

        if os.path.exists(token_path):
            gui_log(f"      ✅ token.json ENCONTRADO em: {token_path}")
            gui_log("      → Vai usar token existente (NÃO abre navegador)")
        else:
            gui_log(f"      ⚠️ token.json NÃO EXISTE em: {token_path}")
            gui_log("      → VAI ABRIR O NAVEGADOR AGORA PARA FAZER LOGIN!")

        gui_log("")
        gui_log("[4/5] Chamando get_sheets_service()...")
        gui_log("      Aguarde... (pode demorar se for abrir navegador)")
        gui_log("")

        service = get_sheets_service()

        gui_log("")
        gui_log("[5/5] ✅ GOOGLE SHEETS AUTENTICADO COM SUCESSO!")
        gui_log("")
        gui_log("=" * 70)
        gui_log("✅ AUTENTICAÇÃO CONCLUÍDA")
        gui_log("=" * 70)
        gui_log("")

    except Exception as e:
        gui_log("")
        gui_log("=" * 70)
        gui_log(f"❌ ERRO NA AUTENTICAÇÃO: {e}")
        gui_log("=" * 70)
        import traceback
        tb = traceback.format_exc()
        for linha in tb.split('\n'):
            if linha.strip():
                gui_log(linha)
        gui_log("")
        gui_log("⚠️ Loop NÃO vai iniciar!")
        gui_log("=" * 70)
        return

    # Registrar ESC para parar
    keyboard.on_press_key('esc', lambda _: parar_rpa())

    gui_log("")
    gui_log("=" * 70)
    gui_log(f"[DEBUG] Verificando _rpa_running antes do loop: {_rpa_running}")
    gui_log("=" * 70)
    gui_log("")

    if not _rpa_running:
        gui_log("=" * 70)
        gui_log("❌ ERRO CRÍTICO: _rpa_running está FALSE!")
        gui_log("❌ O loop NÃO vai iniciar!")
        gui_log("=" * 70)
        return

    gui_log("=" * 70)
    gui_log("✅ _rpa_running está TRUE - Iniciando loop...")
    gui_log("=" * 70)
    gui_log("")

    while _rpa_running:
        try:
            _ciclo_numero += 1

            gui_log("")
            gui_log("╔" + "═" * 68 + "╗")
            gui_log(f"║  🔄 CICLO #{_ciclo_numero:<58} ║")
            gui_log("╚" + "═" * 68 + "╝")
            gui_log("")

            # PASSO 1: ABRIR BANCADA
            gui_log("📍 [PASSO 1/3] ABRINDO BANCADA DE MATERIAL...")
            abrir_bancada()

            # PASSO 2: EXTRAIR DADOS
            gui_log("")
            gui_log("📍 [PASSO 2/3] EXTRAINDO DADOS DA BANCADA...")
            executar_bancada()

            # PASSO 3: FECHAR BANCADA
            gui_log("")
            gui_log("📍 [PASSO 3/3] FECHANDO BANCADA...")
            fechar_bancada()

            # CICLO CONCLUÍDO
            gui_log("")
            gui_log("╔" + "═" * 68 + "╗")
            gui_log(f"║  ✅ CICLO #{_ciclo_numero} CONCLUÍDO!{' ' * (68 - 26 - len(str(_ciclo_numero)))}║")
            gui_log("╚" + "═" * 68 + "╝")
            gui_log("")
            gui_log("🔁 LOOP INFINITO - Próximo ciclo em 2 segundos...")
            gui_log("")

            # Aguardar 2 segundos antes de próximo ciclo
            aguardar_com_pausa(2, "")

        except Exception as e:
            gui_log("")
            gui_log("❌ ERRO NO CICLO: " + str(e))
            gui_log("🔄 Continuando loop em 5 segundos...")
            time.sleep(5)

    gui_log("")
    gui_log("=" * 70)
    gui_log("🏁 LOOP DA BANCADA FINALIZADO")
    gui_log(f"📊 Total de ciclos executados: {_ciclo_numero}")
    gui_log("=" * 70)

    # Remover hook do ESC
    try:
        keyboard.unhook_all()
    except:
        pass

def parar_rpa():
    """Para o RPA"""
    global _rpa_running

    if _rpa_running:
        gui_log("")
        gui_log("━" * 70)
        gui_log("⚠️  PARANDO RPA (ESC PRESSIONADO)...")
        gui_log("━" * 70)
        _rpa_running = False

# =================== GUI ===================
def criar_gui():
    """Cria interface gráfica simples"""
    global _gui_log_widget

    app = tk.Tk()
    app.title("RPA Bancada Loop - Extração Contínua")
    app.geometry("900x600")

    # Frame superior (controles)
    frame_controles = tk.Frame(app, bg="#2c3e50", padx=10, pady=10)
    frame_controles.pack(fill=tk.X)

    # Label título
    label_titulo = tk.Label(
        frame_controles,
        text="🔄 RPA BANCADA LOOP - Extração Contínua (SEM DORMIR)",
        font=("Arial", 14, "bold"),
        bg="#2c3e50",
        fg="white"
    )
    label_titulo.pack(pady=5)

    # Label contador
    label_ciclos = tk.Label(
        frame_controles,
        text="Ciclos: 0",
        font=("Arial", 12),
        bg="#2c3e50",
        fg="#ecf0f1"
    )
    label_ciclos.pack(pady=2)

    # Função para atualizar contador
    def atualizar_contador():
        if app.winfo_exists():
            label_ciclos.config(text=f"Ciclos: {_ciclo_numero}")
            app.after(1000, atualizar_contador)

    # Frame botões
    frame_botoes = tk.Frame(frame_controles, bg="#2c3e50")
    frame_botoes.pack(pady=10)

    def iniciar_rpa_thread():
        global _rpa_running

        if _rpa_running:
            messagebox.showwarning("Aviso", "RPA já está em execução!")
            return

        _rpa_running = True
        btn_iniciar.config(state=tk.DISABLED)
        btn_parar.config(state=tk.NORMAL)

        # Iniciar em thread separada
        thread = threading.Thread(target=executar_loop_bancada, daemon=True)
        thread.start()

        # Iniciar atualização do contador
        atualizar_contador()

    def parar_rpa_gui():
        parar_rpa()
        btn_iniciar.config(state=tk.NORMAL)
        btn_parar.config(state=tk.DISABLED)

    # Botões
    btn_iniciar = tk.Button(
        frame_botoes,
        text="▶ INICIAR LOOP",
        font=("Arial", 12, "bold"),
        bg="#27ae60",
        fg="white",
        padx=20,
        pady=10,
        command=iniciar_rpa_thread
    )
    btn_iniciar.pack(side=tk.LEFT, padx=5)

    btn_parar = tk.Button(
        frame_botoes,
        text="⏹ PARAR (ESC)",
        font=("Arial", 12, "bold"),
        bg="#e74c3c",
        fg="white",
        padx=20,
        pady=10,
        command=parar_rpa_gui,
        state=tk.DISABLED
    )
    btn_parar.pack(side=tk.LEFT, padx=5)

    # Frame log
    frame_log = tk.Frame(app, bg="#34495e", padx=10, pady=10)
    frame_log.pack(fill=tk.BOTH, expand=True)

    label_log = tk.Label(
        frame_log,
        text="📋 LOG DE ATIVIDADES",
        font=("Arial", 10, "bold"),
        bg="#34495e",
        fg="white"
    )
    label_log.pack(anchor=tk.W, pady=(0, 5))

    # Widget de log
    _gui_log_widget = scrolledtext.ScrolledText(
        frame_log,
        wrap=tk.WORD,
        font=("Consolas", 9),
        bg="#1e1e1e",
        fg="#00ff00",
        insertbackground="white",
        state=tk.NORMAL
    )
    _gui_log_widget.pack(fill=tk.BOTH, expand=True)

    # Redirecionar stdout para a GUI (captura prints do Google Sheets)
    sys.stdout = StdoutRedirector(_gui_log_widget)

    # Mensagem inicial
    gui_log("=" * 70)
    gui_log("🔄 RPA BANCADA LOOP - Sistema de Extração Contínua")
    gui_log("=" * 70)
    gui_log("")
    gui_log("INSTRUÇÕES:")
    gui_log("1. Certifique-se que o Oracle está aberto e logado")
    gui_log("2. Clique em 'INICIAR LOOP' para começar")
    gui_log("3. O sistema irá executar em loop infinito:")
    gui_log("   • Abrir Bancada de Material")
    gui_log("   • Extrair dados (Detalhado + Copiar)")
    gui_log("   • Salvar Excel local")
    gui_log("   • Enviar para Google Sheets")
    gui_log("   • Fechar bancada")
    gui_log("   • Repetir")
    gui_log("4. Pressione ESC ou clique 'PARAR' para interromper")
    gui_log("")
    gui_log("⚠️ PROTEÇÃO ANTI-HIBERNAÇÃO ATIVA")
    gui_log("   • Mouse se move automaticamente")
    gui_log("   • Shift pressionado periodicamente")
    gui_log("   • Sistema NUNCA vai dormir durante execução")
    gui_log("")
    gui_log("=" * 70)
    gui_log("")

    # Fechar aplicação
    def on_closing():
        if _rpa_running:
            if messagebox.askokcancel("Sair", "RPA está rodando. Deseja parar e sair?"):
                parar_rpa()
                app.destroy()
        else:
            app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()

# =================== MAIN ===================
if __name__ == "__main__":
    criar_gui()
