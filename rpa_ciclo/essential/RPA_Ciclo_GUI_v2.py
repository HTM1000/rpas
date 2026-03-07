# -*- coding: utf-8 -*-
"""
RPA CICLO - Interface Gráfica Modernizada v2
Sistema de automação de ciclo completo Oracle + Bancada
Com histórico de Excel e acesso às movimentações
"""

import threading
import time
import os
import sys
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import subprocess
from pathlib import Path
from datetime import datetime
import glob

# Importar o módulo principal do RPA
import main_ciclo as main

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent

# Estado global do RPA
estado = {
    "executando": False,
    "thread_rpa": None,
    "modo_continuo": False
}

# ─── HELPERS DE UI ──────────────────────────────────────────────────────────
def set_title_running(is_running: bool, extra: str = ""):
    """Atualiza o título da janela conforme o status"""
    base = "RPA Ciclo Automação"
    sufixo = " [Rodando]" if is_running else " [Parado]"
    try:
        app.title(f"{base}{sufixo}{extra}")
    except Exception:
        pass

def restaurar_app():
    """Restaura a janela se minimizada"""
    try:
        app.deiconify()
        app.lift()
        try:
            app.focus_force()
        except Exception:
            pass
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

# ─── HISTÓRICO DE ARQUIVOS ──────────────────────────────────────────────────
def atualizar_historico_excel():
    """Atualiza a lista de arquivos Excel gerados (Oracle + Bancada)"""
    try:
        # Limpar lista atual
        historico_listbox.delete(0, tk.END)

        arquivos_encontrados = []

        # 1. Buscar arquivos da pasta de exportações do Oracle (rpa_oracle/exportacoes)
        pasta_oracle = BASE_DIR.parent / "rpa_oracle" / "exportacoes"
        if pasta_oracle.exists():
            for arquivo in pasta_oracle.glob("export_sessao_*.csv"):
                stat = arquivo.stat()
                data_modificacao = datetime.fromtimestamp(stat.st_mtime)
                arquivos_encontrados.append({
                    "tipo": "Oracle",
                    "nome": arquivo.name,
                    "caminho": str(arquivo),
                    "data": data_modificacao,
                    "tamanho": stat.st_size
                })

        # 2. Buscar arquivos da pasta out do Bancada (dentro de Genesys)
        pasta_bancada = BASE_DIR / "rpa_bancada" / "out"
        if pasta_bancada.exists():
            for arquivo in pasta_bancada.glob("bancada_*.xlsx"):
                stat = arquivo.stat()
                data_modificacao = datetime.fromtimestamp(stat.st_mtime)
                arquivos_encontrados.append({
                    "tipo": "Bancada",
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
            tipo_icon = "📊" if arquivo["tipo"] == "Oracle" else "📋"
            linha = f"{tipo_icon} [{arquivo['tipo']}] {arquivo['nome']} - {data_str} ({tamanho_kb:.1f} KB)"
            historico_listbox.insert(tk.END, linha)
            # Armazenar o caminho do arquivo como atributo invisível
            historico_listbox.itemconfig(tk.END, {"tags": arquivo["caminho"]})

        # Atualizar contador
        label_contador_historico.config(text=f"Total: {len(arquivos_encontrados)} arquivos")

        log_interface(f"📂 Histórico atualizado: {len(arquivos_encontrados)} arquivos encontrados")

    except Exception as e:
        log_interface(f"❌ Erro ao atualizar histórico: {e}")
        messagebox.showerror("Erro", f"Erro ao atualizar histórico:\n{e}")

def abrir_arquivo_selecionado(event=None):
    """Abre o arquivo Excel selecionado no histórico"""
    try:
        selecao = historico_listbox.curselection()
        if not selecao:
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado!")
            return

        # Pegar o caminho do arquivo pelas tags (precisa usar approach diferente)
        # Na verdade, vamos refazer usando um dicionário
        # Por ora, vamos extrair do texto
        idx = selecao[0]
        texto = historico_listbox.get(idx)

        # Extrair nome do arquivo do texto
        # Formato: "📊 [Oracle] export_sessao_20251018_143025.csv - 18/10/2025 14:30:25 (12.5 KB)"
        partes = texto.split("] ", 1)
        if len(partes) < 2:
            return

        tipo = "Oracle" if "[Oracle]" in texto else "Bancada"
        nome_arquivo = partes[1].split(" - ")[0]

        # Reconstruir caminho
        if tipo == "Oracle":
            caminho = BASE_DIR.parent / "rpa_oracle" / "exportacoes" / nome_arquivo
        else:
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

def abrir_pasta_movimentacoes_oracle():
    """Abre a pasta de movimentações (exportações) do RPA_Oracle"""
    try:
        pasta_oracle = BASE_DIR.parent / "rpa_oracle" / "exportacoes"
        pasta_oracle.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(str(pasta_oracle))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(pasta_oracle)])
        else:
            subprocess.Popen(["xdg-open", str(pasta_oracle)])

        log_interface(f"📂 Pasta Oracle aberta: {pasta_oracle}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta Oracle: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def abrir_pasta_excel_bancada():
    """Abre a pasta de Excel gerados pelo RPA_Bancada"""
    try:
        # Criar dentro de Genesys/
        pasta_bancada = BASE_DIR / "rpa_bancada" / "out"
        pasta_bancada.mkdir(parents=True, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(str(pasta_bancada))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(pasta_bancada)])
        else:
            subprocess.Popen(["xdg-open", str(pasta_bancada)])

        log_interface(f"📂 Pasta Bancada aberta: {pasta_bancada}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta Bancada: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def abrir_google_sheets_oracle():
    """Abre a planilha do Google Sheets do Oracle"""
    try:
        url = "https://docs.google.com/spreadsheets/d/147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY/edit"

        if sys.platform.startswith("win"):
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])

        log_interface("☁️ Google Sheets Oracle aberto no navegador")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir Google Sheets Oracle: {e}")

def abrir_google_sheets_ciclo():
    """Abre a planilha do Google Sheets do Ciclo (histórico de execuções)"""
    try:
        url = "https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit"

        if sys.platform.startswith("win"):
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])

        log_interface("☁️ Google Sheets Ciclo aberto no navegador")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir Google Sheets Ciclo: {e}")

# ─── CONTROLE DO RPA ────────────────────────────────────────────────────────
def rpa_worker():
    """Thread worker que executa o RPA principal"""
    try:
        # Configurar callback de log para a GUI
        main.set_gui_log_callback(log_interface)

        modo = "CONTÍNUO (repete automaticamente)" if estado["modo_continuo"] else "ÚNICA EXECUÇÃO"
        log_interface(f"🚀 RPA iniciado - Modo: {modo}")
        log_interface("⚠️ FAILSAFE ativo: mova o mouse para o canto superior esquerdo para parar")

        # Chama a função main do RPA
        main.main(modo_continuo=estado["modo_continuo"])

        # Quando terminar, mostrar notificação
        log_interface("=" * 70)
        log_interface("✅ RPA FINALIZADO")
        log_interface("=" * 70)

        mensagem = "Automação finalizada!\n\n"
        if estado["modo_continuo"]:
            mensagem += "Modo contínuo foi interrompido.\nClique em 'Iniciar RPA' para nova execução."
        else:
            mensagem += "Ciclo único concluído.\nClique em 'Iniciar RPA' para executar novamente."

        # Atualizar histórico de arquivos ao finalizar
        app.after(0, lambda: atualizar_historico_excel())

        app.after(0, lambda: messagebox.showinfo("RPA Concluído", mensagem))

    except KeyboardInterrupt:
        log_interface("🛑 RPA interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        log_interface(f"❌ Erro no RPA: {e}")
        import traceback
        log_interface(traceback.format_exc())
        app.after(0, lambda: messagebox.showerror("Erro RPA", f"Erro durante execução do RPA:\n{e}"))
    finally:
        # Atualizar estado quando terminar
        estado["executando"] = False
        estado["thread_rpa"] = None
        app.after(0, lambda: atualizar_interface_parado())

        # Restaurar janela para o usuário ver que terminou
        app.after(100, lambda: restaurar_app())

def atualizar_interface_parado():
    """Atualiza interface quando RPA para"""
    btn_iniciar_unico.config(state='normal')
    btn_iniciar_continuo.config(state='normal')
    btn_parar.config(state='disabled')
    status_label.config(text="Status: Parado", fg="red")
    set_title_running(False)
    log_interface("⸏ RPA parado")

def iniciar_rpa(modo_continuo=False):
    """Inicia o RPA em thread separada"""
    if estado["executando"]:
        messagebox.showwarning("Aviso", "RPA já está em execução!")
        return

    modo_str = "contínuo (repete automaticamente)" if modo_continuo else "execução única"

    # Confirmação
    resposta = messagebox.askyesno(
        "Confirmar Início",
        f"Modo: {modo_str.upper()}\n\n"
        "Certifique-se de que:\n\n"
        "✓ Oracle Applications está aberto\n"
        "✓ Você está na tela inicial correta\n"
        "✓ A resolução está adequada\n\n"
        "Deseja iniciar o RPA?"
    )

    if not resposta:
        return

    # Minimizar janela
    app.iconify()

    # Atualizar estado
    estado["executando"] = True
    estado["modo_continuo"] = modo_continuo
    btn_iniciar_unico.config(state='disabled')
    btn_iniciar_continuo.config(state='disabled')
    btn_parar.config(state='normal')
    status_label.config(text=f"Status: Rodando ({modo_str})", fg="green")
    set_title_running(True)

    # Limpar log
    log_text.config(state='normal')
    log_text.delete(1.0, 'end')
    log_text.config(state='disabled')

    # Iniciar thread do RPA
    estado["thread_rpa"] = threading.Thread(target=rpa_worker, daemon=True)
    estado["thread_rpa"].start()

    log_interface(f"▶️ Iniciando RPA em modo {modo_str}...")

def parar_rpa():
    """Para o RPA"""
    if not estado["executando"]:
        messagebox.showinfo("Info", "RPA não está em execução!")
        return

    # Sinalizar parada no módulo main
    estado["executando"] = False
    main.stop_rpa()

    log_interface("🛑 Solicitando parada do RPA...")

    # Restaurar interface
    restaurar_app()

    # Atualizar interface
    atualizar_interface_parado()

def mostrar_ajuda():
    """Mostra janela de ajuda"""
    ajuda_window = tk.Toplevel(app)
    ajuda_window.title("Ajuda - RPA Ciclo Automação")
    ajuda_window.geometry("700x600")
    ajuda_window.resizable(False, False)

    # Texto de ajuda
    ajuda_text = scrolledtext.ScrolledText(ajuda_window, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 9))
    ajuda_text.pack(fill=tk.BOTH, expand=True)

    help_content = """
🤖 RPA CICLO AUTOMAÇÃO v2.0 - AJUDA

📋 FUNCIONALIDADES:
• Automação completa do ciclo Oracle (Oracle + Bancada)
• Execução automática do RPA_Oracle (processa movimentações)
• Execução automática do RPA_Bancada (extrai dados da bancada)
• Histórico completo de arquivos Excel gerados
• Acesso rápido às pastas de movimentações
• Registro de logs no Google Sheets
• Modo contínuo (repete automaticamente)

🚀 COMO USAR:

1. PREPARAÇÃO:
   - Abra o Oracle Applications
   - Navegue até a tela inicial da Transferência de Subinventário
   - Certifique-se de que a resolução está em 1440x900 (recomendado)

2. EXECUÇÃO ÚNICA:
   - Clique em "🎯 Ciclo Único"
   - O RPA executará todas as etapas uma vez
   - Ao finalizar, você pode executar novamente

3. EXECUÇÃO CONTÍNUA:
   - Clique em "🔄 Modo Contínuo"
   - O RPA executará as etapas repetidamente
   - Pressione "⏹️ Parar RPA" para interromper

📊 HISTÓRICO DE EXCEL:
• Mostra todos os arquivos Excel gerados (Oracle + Bancada)
• Duplo clique em um arquivo para abrir
• Ordenados do mais recente para o mais antigo
• Limitado aos 50 arquivos mais recentes
• Use "🔄 Atualizar" para recarregar a lista

📂 PASTAS E MOVIMENTAÇÕES:
• "📊 Movimentações Oracle" - Abre pasta de exportações do RPA_Oracle
• "📋 Excel Bancada" - Abre pasta out do RPA_Bancada
• "☁️ Sheets Oracle" - Abre planilha de separação do Google Sheets
• "☁️ Sheets Ciclo" - Abre planilha de histórico de execuções

🔒 SEGURANÇA:
• FAILSAFE: Mova o mouse para o canto superior esquerdo para parar
• Botão "⏹️ Parar RPA" para interrupção manual
• Logs salvos automaticamente
• Dados sempre salvos localmente como backup

📊 ETAPAS DO CICLO:
1. Transferência de Subinventário
2. Preenchimento do campo Tipo (SUB)
3. Seleção de Funcionário (Wallatas Moreira)
4. Confirmação
5. Execução do RPA_Oracle (processa linhas do Google Sheets)
6. Navegação pós-Oracle
7. Abertura da Bancada de Material
8. Execução do RPA_Bancada (extrai dados e salva em Excel)
9. Fechamento da Bancada
10. Reinicia o ciclo (apenas no modo contínuo)

☁️ GOOGLE SHEETS:
• Todos os ciclos são registrados automaticamente
• Informações registradas:
  - Data/Hora de Início e Fim
  - Número do Ciclo
  - Status (Sucesso/Falha/Pausado)
  - Tempo de Execução
  - Etapa que falhou (se houver)
  - Status do RPA Oracle
  - Status do RPA Bancada

🔧 TROUBLESHOOTING:
• Se elementos não forem encontrados: Verifique resolução da tela
• Se falhar Google Sheets: Verifique credenciais e token.json
• Para problemas de coordenadas: Edite config.json
• Se RPA_Oracle/Bancada falharem: Verifique se os processos estão acessíveis

📞 INFORMAÇÕES:
• Versão: 2.0
• Data: Outubro 2025
• Desenvolvido para automação completa do ciclo Oracle
• Integra RPA_Oracle + RPA_Bancada em um único fluxo
    """

    ajuda_text.insert(1.0, help_content)
    ajuda_text.config(state='disabled')

    # Botão fechar
    tk.Button(ajuda_window, text="Fechar", command=ajuda_window.destroy, font=("Arial", 10), bg="#2196F3", fg="white").pack(pady=10)

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Ciclo Automação v2.0")
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
    tk.Label(logo_frame, text="RPA CICLO AUTOMAÇÃO", font=("Arial", 14, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONTROLES ──────────────────────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=8)

# Botões principais
btn_iniciar_unico = tk.Button(
    controls_frame,
    text="🎯 Ciclo Único",
    command=lambda: iniciar_rpa(modo_continuo=False),
    font=("Arial", 10, "bold"),
    bg="#2196F3",
    fg="white",
    padx=12,
    pady=8,
    width=13
)
btn_iniciar_unico.pack(side="left", padx=4)

btn_iniciar_continuo = tk.Button(
    controls_frame,
    text="🔄 Modo Contínuo",
    command=lambda: iniciar_rpa(modo_continuo=True),
    font=("Arial", 10, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=12,
    pady=8,
    width=13
)
btn_iniciar_continuo.pack(side="left", padx=4)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar RPA",
    command=parar_rpa,
    font=("Arial", 10, "bold"),
    bg="#f44336",
    fg="white",
    padx=12,
    pady=8,
    width=13,
    state='disabled'
)
btn_parar.pack(side="left", padx=4)

# ─── ÁREA DE UTILITÁRIOS (PASTAS E GOOGLE SHEETS) ───────────────────────────
utils_frame = tk.Frame(app)
utils_frame.pack(pady=8)

tk.Button(
    utils_frame,
    text="📊 Movimentações Oracle",
    command=abrir_pasta_movimentacoes_oracle,
    font=("Arial", 9),
    bg="#FF9800",
    fg="white",
    padx=10,
    pady=4
).pack(side="left", padx=3)

tk.Button(
    utils_frame,
    text="📋 Excel Bancada",
    command=abrir_pasta_excel_bancada,
    font=("Arial", 9),
    bg="#9C27B0",
    fg="white",
    padx=10,
    pady=4
).pack(side="left", padx=3)

tk.Button(
    utils_frame,
    text="❓ Ajuda",
    command=mostrar_ajuda,
    font=("Arial", 9),
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

# ─── DIVISOR ENTRE SEÇÕES ───────────────────────────────────────────────────
separator1 = ttk.Separator(app, orient='horizontal')
separator1.pack(fill='x', padx=20, pady=5)

# ─── ÁREA DE HISTÓRICO DE EXCEL ─────────────────────────────────────────────
historico_frame = tk.Frame(app)
historico_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=False)

# Cabeçalho do histórico
historico_header = tk.Frame(historico_frame)
historico_header.pack(fill=tk.X)

tk.Label(historico_header, text="📂 Histórico de Excel Gerados:", font=("Arial", 10, "bold")).pack(side="left")

label_contador_historico = tk.Label(historico_header, text="Total: 0 arquivos", font=("Arial", 9), fg="gray")
label_contador_historico.pack(side="left", padx=10)

btn_atualizar_historico = tk.Button(
    historico_header,
    text="🔄 Atualizar",
    command=atualizar_historico_excel,
    font=("Arial", 8),
    bg="#4CAF50",
    fg="white",
    padx=8,
    pady=2
)
btn_atualizar_historico.pack(side="right")

# Listbox com scrollbar para histórico
historico_scroll = tk.Scrollbar(historico_frame, orient=tk.VERTICAL)
historico_listbox = tk.Listbox(
    historico_frame,
    height=6,
    width=100,
    font=("Consolas", 8),
    yscrollcommand=historico_scroll.set,
    bg="#f8f8f8"
)
historico_scroll.config(command=historico_listbox.yview)
historico_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5, 0))
historico_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(5, 0))

# Bind duplo clique para abrir arquivo
historico_listbox.bind("<Double-Button-1>", abrir_arquivo_selecionado)

tk.Label(historico_frame, text="💡 Duplo clique em um arquivo para abrir", font=("Arial", 8), fg="gray").pack(anchor="w", pady=(2, 0))

# ─── DIVISOR ENTRE SEÇÕES ───────────────────────────────────────────────────
separator2 = ttk.Separator(app, orient='horizontal')
separator2.pack(fill='x', padx=20, pady=5)

# ─── ÁREA DE LOG ────────────────────────────────────────────────────────────
log_frame = tk.Frame(app)
log_frame.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

tk.Label(log_frame, text="📋 Log de Execução:", font=("Arial", 10, "bold")).pack(anchor="w")

# Text widget com scrollbar
log_text = scrolledtext.ScrolledText(
    log_frame,
    height=15,
    width=100,
    wrap=tk.WORD,
    state='disabled',
    font=("Consolas", 8),
    bg="#f8f8f8"
)
log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

# ─── INICIALIZAÇÃO ──────────────────────────────────────────────────────────
# Ajusta o título inicial
set_title_running(False)

# Log inicial
log_interface("🤖 RPA Ciclo Automação v2.0 carregado")
log_interface("✅ Sistema pronto para iniciar")
log_interface("📖 Clique em 'Ajuda' para instruções detalhadas")
log_interface("")
log_interface("Escolha o modo de execução:")
log_interface("  🎯 Ciclo Único - Executa uma vez e para")
log_interface("  🔄 Modo Contínuo - Repete automaticamente")

# Carregar histórico de Excel ao iniciar
atualizar_historico_excel()

# Interceptar fechamento da janela
def on_closing():
    if estado["executando"]:
        resposta = messagebox.askyesno(
            "Confirmar Saída",
            "RPA está em execução. Deseja realmente sair?\n\n"
            "Isso interromperá a automação."
        )
        if not resposta:
            return

        # Parar RPA se estiver rodando
        parar_rpa()

    # Destruir janela
    app.destroy()

    # CRÍTICO: Forçar terminação do processo (evita ficar em background)
    import sys
    sys.exit(0)

app.protocol("WM_DELETE_WINDOW", on_closing)

# ─── EXECUÇÃO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.mainloop()
