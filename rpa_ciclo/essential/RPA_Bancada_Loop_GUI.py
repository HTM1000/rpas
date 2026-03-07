#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA BANCADA LOOP - Interface Gráfica v1.0
Sistema de extração contínua da Bancada de Material
Loop infinito com proteção anti-hibernação
"""

import threading
import time
import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import subprocess
from pathlib import Path
from datetime import datetime

# Importar o módulo de execução da bancada
import RPA_Bancada_Loop as bancada_loop

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent

# Estado global do RPA
estado = {
    "executando": False,
    "thread_rpa": None,
    "ciclos_executados": 0
}

# ─── HELPERS DE UI ──────────────────────────────────────────────────────────
def set_title_running(is_running: bool):
    """Atualiza o título da janela conforme o status"""
    base = "RPA Bancada Loop"
    sufixo = " [Rodando]" if is_running else " [Parado]"
    try:
        app.title(f"{base}{sufixo}")
    except Exception:
        pass

def log_interface(msg: str):
    """Adiciona mensagem ao log da interface"""
    try:
        log_text.config(state='normal')
        log_text.insert('end', f"{time.strftime('%H:%M:%S')} - {msg}\n")
        log_text.see('end')
        log_text.config(state='disabled')
        app.update_idletasks()
    except Exception:
        pass

def atualizar_contador_ciclos():
    """Atualiza o contador de ciclos na interface"""
    try:
        label_contador.config(text=f"Ciclos Executados: {bancada_loop._ciclo_numero}")
        app.after(1000, atualizar_contador_ciclos)
    except:
        pass

# ─── HISTÓRICO DE ARQUIVOS ──────────────────────────────────────────────────
def atualizar_historico_excel():
    """Atualiza a lista de arquivos Excel gerados pela Bancada"""
    try:
        # Limpar lista atual
        historico_listbox.delete(0, tk.END)

        arquivos_encontrados = []

        # Buscar arquivos da pasta out do Bancada
        pasta_bancada = BASE_DIR / "rpa_bancada" / "out"
        if pasta_bancada.exists():
            for arquivo in pasta_bancada.glob("bancada*.xlsx"):
                stat = arquivo.stat()
                data_modificacao = datetime.fromtimestamp(stat.st_mtime)
                arquivos_encontrados.append({
                    "nome": arquivo.name,
                    "caminho": str(arquivo),
                    "data": data_modificacao,
                    "tamanho": stat.st_size
                })

        # Ordenar por data (mais recente primeiro)
        arquivos_encontrados.sort(key=lambda x: x["data"], reverse=True)

        # Adicionar à listbox (limitar aos 50 mais recentes)
        for arquivo in arquivos_encontrados[:50]:
            data_str = arquivo["data"].strftime("%d/%m/%Y %H:%M:%S")
            tamanho_kb = arquivo["tamanho"] / 1024
            linha = f"📋 {arquivo['nome']} - {data_str} ({tamanho_kb:.1f} KB)"
            historico_listbox.insert(tk.END, linha)

        # Atualizar contador
        label_contador_historico.config(text=f"Total: {len(arquivos_encontrados)} arquivos")

        log_interface(f"📂 Histórico atualizado: {len(arquivos_encontrados)} arquivos encontrados")

    except Exception as e:
        log_interface(f"❌ Erro ao atualizar histórico: {e}")

def abrir_arquivo_selecionado(event=None):
    """Abre o arquivo Excel selecionado no histórico"""
    try:
        selecao = historico_listbox.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
            return

        idx = selecao[0]
        texto = historico_listbox.get(idx)

        # Extrair nome do arquivo
        nome_arquivo = texto.split(" - ")[0].replace("📋 ", "")

        # Caminho do arquivo
        caminho = BASE_DIR / "rpa_bancada" / "out" / nome_arquivo

        if caminho.exists():
            if sys.platform.startswith("win"):
                os.startfile(str(caminho))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(caminho)])
            else:
                subprocess.Popen(["xdg-open", str(caminho)])

            log_interface(f"📂 Arquivo aberto: {caminho.name}")
        else:
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{caminho}")

    except Exception as e:
        log_interface(f"❌ Erro ao abrir arquivo: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir arquivo:\n{e}")

def abrir_pasta_excel_bancada():
    """Abre a pasta de Excel gerados pelo RPA_Bancada"""
    try:
        pasta_bancada = BASE_DIR / "rpa_bancada" / "out"
        pasta_bancada.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(str(pasta_bancada))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(pasta_bancada)])
        else:
            subprocess.Popen(["xdg-open", str(pasta_bancada)])

        log_interface(f"📂 Pasta Excel aberta: {pasta_bancada}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

# ─── CONTROLE DO RPA ────────────────────────────────────────────────────────
def iniciar_rpa():
    """Inicia o RPA Bancada Loop"""
    if estado["executando"]:
        messagebox.showwarning("Aviso", "RPA já está em execução!")
        return

    log_interface("=" * 70)
    log_interface("🚀 INICIANDO RPA BANCADA LOOP")
    log_interface("=" * 70)

    estado["executando"] = True
    bancada_loop._rpa_running = True
    bancada_loop._ciclo_numero = 0

    # Conectar log do módulo à interface
    bancada_loop._gui_log_widget = log_text

    # Atualizar UI
    btn_iniciar.config(state='disabled')
    btn_parar.config(state='normal')
    status_label.config(text="Status: Rodando em Loop Infinito", fg="green")
    set_title_running(True)

    # Iniciar atualização do contador
    atualizar_contador_ciclos()

    # Função que será executada em thread separada
    def executar_thread():
        try:
            bancada_loop.executar_loop_bancada()
        except Exception as e:
            log_interface(f"❌ ERRO CRÍTICO: {e}")
            import traceback
            log_interface(traceback.format_exc())
        finally:
            # Finalizar
            estado["executando"] = False
            bancada_loop._rpa_running = False

            # Restaurar UI
            try:
                btn_iniciar.config(state='normal')
                btn_parar.config(state='disabled')
                status_label.config(text="Status: Parado", fg="orange")
                set_title_running(False)
            except:
                pass

            # Atualizar histórico
            try:
                atualizar_historico_excel()
            except:
                pass

            log_interface("=" * 70)
            log_interface("🏁 RPA FINALIZADO")
            log_interface("=" * 70)

    # Iniciar thread
    estado["thread_rpa"] = threading.Thread(target=executar_thread, daemon=True)
    estado["thread_rpa"].start()

def parar_rpa():
    """Para o RPA"""
    if not estado["executando"]:
        messagebox.showwarning("Aviso", "RPA não está em execução!")
        return

    if messagebox.askyesno("Confirmar", "Deseja realmente parar o RPA?"):
        log_interface("⚠️ PARANDO RPA...")
        bancada_loop.parar_rpa()

        btn_iniciar.config(state='normal')
        btn_parar.config(state='disabled')
        status_label.config(text="Status: Parando...", fg="red")

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Bancada Loop v1.0")
app.geometry("750x700")
app.resizable(False, False)

# Ícone da janela
try:
    icone_path = os.path.join(base_path, "Topo.png")
    if os.path.exists(icone_path):
        app.iconphoto(True, ImageTk.PhotoImage(file=icone_path))
except Exception as e:
    print(f"Erro ao definir ícone: {e}")

# ─── ÁREA DOS LOGOS ─────────────────────────────────────────────────────────
try:
    logo_frame = tk.Frame(app, bg="#f7f7f7")
    logo_frame.pack(pady=(15, 10), fill=tk.X)

    # Logo Genesys
    logo1_path = os.path.join(base_path, "Logo.png")
    if os.path.exists(logo1_path):
        logo1_img = Image.open(logo1_path).resize((130, 80))
        logo1_tk = ImageTk.PhotoImage(logo1_img)

        # Logo Tecumseh
        logo2_path = os.path.join(base_path, "Tecumseh.png")
        if os.path.exists(logo2_path):
            logo2_img = Image.open(logo2_path).resize((80, 60))
            logo2_tk = ImageTk.PhotoImage(logo2_img)

            # Container centralizado para os logos
            logos_container = tk.Frame(logo_frame, bg="#f7f7f7")
            logos_container.pack()

            tk.Label(logos_container, image=logo1_tk, bg="#f7f7f7").pack(side="left", padx=12)
            tk.Label(logos_container, image=logo2_tk, bg="#f7f7f7").pack(side="left", padx=12)
        else:
            raise FileNotFoundError("Logo Tecumseh não encontrado")
    else:
        raise FileNotFoundError("Logo Genesys não encontrado")

except Exception as e:
    print(f"❌ Erro ao carregar logos: {e}")
    # Frame vazio se logos falharem
    logo_frame = tk.Frame(app, height=80, bg="#f7f7f7")
    logo_frame.pack(pady=(15, 10), fill=tk.X)
    tk.Label(logo_frame, text="RPA BANCADA LOOP", font=("Arial", 14, "bold"), bg="#f7f7f7").pack()

# Título
titulo_frame = tk.Frame(app, bg="#f7f7f7")
titulo_frame.pack(pady=5)
tk.Label(titulo_frame, text="🔄 EXTRAÇÃO CONTÍNUA DA BANCADA",
         font=("Arial", 12, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONTROLES ──────────────────────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=8)

# Botões principais
btn_iniciar = tk.Button(
    controls_frame,
    text="▶️ INICIAR LOOP",
    command=iniciar_rpa,
    font=("Arial", 11, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    width=15
)
btn_iniciar.pack(side="left", padx=4)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar Loop (ESC)",
    command=parar_rpa,
    font=("Arial", 11, "bold"),
    bg="#f44336",
    fg="white",
    padx=20,
    pady=10,
    width=15,
    state='disabled'
)
btn_parar.pack(side="left", padx=4)

# ─── CONTADOR DE CICLOS ─────────────────────────────────────────────────────
contador_frame = tk.Frame(app, bg="#e3f2fd", bd=2, relief=tk.RIDGE)
contador_frame.pack(pady=8, padx=10, fill=tk.X)

label_contador = tk.Label(
    contador_frame,
    text="Ciclos Executados: 0",
    font=("Arial", 12, "bold"),
    bg="#e3f2fd",
    fg="#1976d2"
)
label_contador.pack(pady=8)

# ─── ÁREA DE UTILITÁRIOS ────────────────────────────────────────────────────
utils_frame = tk.Frame(app)
utils_frame.pack(pady=8)

tk.Button(
    utils_frame,
    text="📋 Abrir Pasta Excel",
    command=abrir_pasta_excel_bancada,
    font=("Arial", 9),
    bg="#9C27B0",
    fg="white",
    padx=10,
    pady=4
).pack(side="left", padx=3)

tk.Button(
    utils_frame,
    text="🔄 Atualizar Histórico",
    command=atualizar_historico_excel,
    font=("Arial", 9),
    bg="#00BCD4",
    fg="white",
    padx=10,
    pady=4
).pack(side="left", padx=3)

# ─── STATUS ─────────────────────────────────────────────────────────────────
status_frame = tk.Frame(app)
status_frame.pack(pady=8)

status_label = tk.Label(
    status_frame,
    text="Status: Aguardando",
    font=("Arial", 11, "bold"),
    fg="orange"
)
status_label.pack()

# ─── ÁREA DO LOG ────────────────────────────────────────────────────────────
log_frame = tk.LabelFrame(app, text="📋 LOG DE ATIVIDADES", font=("Arial", 10, "bold"))
log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

log_text = scrolledtext.ScrolledText(
    log_frame,
    wrap=tk.WORD,
    height=10,
    font=("Consolas", 9),
    bg="#1e1e1e",
    fg="#00ff00",
    state='disabled'
)
log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ─── HISTÓRICO DE ARQUIVOS ──────────────────────────────────────────────────
historico_frame = tk.LabelFrame(app, text="📁 HISTÓRICO DE ARQUIVOS EXCEL", font=("Arial", 10, "bold"))
historico_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

# Contador
label_contador_historico = tk.Label(historico_frame, text="Total: 0 arquivos", font=("Arial", 9))
label_contador_historico.pack(anchor=tk.W, padx=5, pady=2)

# Listbox
historico_listbox = tk.Listbox(
    historico_frame,
    font=("Consolas", 9),
    height=5,
    selectmode=tk.SINGLE
)
historico_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
historico_listbox.bind("<Double-Button-1>", abrir_arquivo_selecionado)

# ─── MENSAGEM INICIAL ───────────────────────────────────────────────────────
log_interface("=" * 70)
log_interface("🔄 RPA BANCADA LOOP - Sistema de Extração Contínua")
log_interface("=" * 70)
log_interface("")
log_interface("INSTRUÇÕES:")
log_interface("1. Certifique-se que o Oracle está aberto e logado")
log_interface("2. Clique em '▶️ INICIAR LOOP' para começar")
log_interface("3. O sistema irá executar em LOOP INFINITO:")
log_interface("   • Abrir Bancada de Material")
log_interface("   • Extrair dados (Detalhado + Copiar)")
log_interface("   • Salvar Excel local")
log_interface("   • Enviar para Google Sheets")
log_interface("   • Fechar bancada")
log_interface("   • Repetir (SEM ESPERA)")
log_interface("4. Pressione ESC ou clique 'Parar' para interromper")
log_interface("")
log_interface("⚠️ PROTEÇÃO ANTI-HIBERNAÇÃO ATIVA")
log_interface("   • Mouse se move automaticamente")
log_interface("   • Shift pressionado periodicamente")
log_interface("   • Sistema NUNCA vai dormir")
log_interface("")
log_interface("=" * 70)
log_interface("")

# Atualizar histórico ao iniciar
atualizar_historico_excel()

# ─── FECHAR APLICAÇÃO ───────────────────────────────────────────────────────
def on_closing():
    if estado["executando"]:
        if messagebox.askokcancel("Sair", "RPA está rodando. Deseja parar e sair?"):
            bancada_loop.parar_rpa()
            time.sleep(1)
            app.destroy()
            sys.exit(0)
    else:
        app.destroy()
        sys.exit(0)

app.protocol("WM_DELETE_WINDOW", on_closing)

# ─── MAIN LOOP ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.mainloop()
