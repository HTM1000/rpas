# -*- coding: utf-8 -*-
"""
RPA INVENTÁRIO - Interface Gráfica
Sistema de automação de inventário via Playwright
"""

import threading
import time
import os
import sys
import json
import socket
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from PIL import Image, ImageTk
import subprocess
from pathlib import Path
from datetime import datetime

# Importar o módulo principal do RPA
import main_inventario as main

# Pegar nome do computador automaticamente
NOME_COMPUTADOR = socket.gethostname()

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent

# Estado global do RPA
estado = {
    "executando": False,
    "thread_rpa": None
}

# ─── HELPERS DE UI ──────────────────────────────────────────────────────────
def set_title_running(is_running: bool, extra: str = ""):
    """Atualiza o título da janela conforme o status"""
    base = "RPA Inventário"
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

# ─── CONTROLE DO RPA ────────────────────────────────────────────────────────
def rpa_worker():
    """Thread worker que executa o RPA principal"""
    try:
        # Configurar callback de log para a GUI
        main.set_gui_log_callback(log_interface)

        inventario = estado.get("inventario", "")
        robo_id = estado.get("robo_id", "PC-01")
        tipo_contagem = estado.get("tipo_contagem", "primeira")
        tipo_planilha = estado.get("tipo_planilha", "bc1")
        modo_teste_ativo = estado.get("modo_teste", False)

        log_interface("🚀 RPA Inventário iniciado")
        log_interface(f"📋 Inventário: {inventario}")
        log_interface(f"🤖 Robô: {robo_id}")
        log_interface(f"📁 Planilha: {tipo_planilha.upper()}")
        log_interface(f"📊 Tipo: {tipo_contagem.title()} Contagem")
        log_interface(f"🧪 Modo Teste: {'ATIVADO' if modo_teste_ativo else 'Desativado'}")
        log_interface("⚠️ Pressione ESC para parar a qualquer momento")

        # Chama a função main do RPA passando os parâmetros
        main.main(inventario=inventario, robo_id=robo_id, tipo_contagem=tipo_contagem, tipo_planilha=tipo_planilha, modo_teste=modo_teste_ativo)

        # Quando terminar, mostrar notificação
        log_interface("=" * 70)
        log_interface("✅ RPA FINALIZADO")
        log_interface("=" * 70)

        mensagem = "Automação finalizada com sucesso!\n\nClique em 'Iniciar RPA' para executar novamente."

        app.after(0, lambda: messagebox.showinfo("RPA Concluído", mensagem))

    except KeyboardInterrupt:
        log_interface("🛑 RPA interrompido pelo usuário (ESC)")
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
    btn_iniciar.config(state='normal')
    btn_parar.config(state='disabled')
    status_label.config(text="Status: Parado", fg="red")
    set_title_running(False)
    log_interface("⸏ RPA parado")

def iniciar_rpa():
    """Inicia o RPA em thread separada"""
    if estado["executando"]:
        messagebox.showwarning("Aviso", "RPA já está em execução!")
        return

    # Validar se inventário foi preenchido
    inventario = entry_inventario.get().strip()
    if not inventario:
        messagebox.showerror("Erro", "Por favor, preencha o nome do inventário!")
        entry_inventario.focus()
        return

    # Pegar ID do robô (nome do computador)
    robo_id = entry_robo_id.get().strip()

    # Pegar tipo de contagem, tipo de planilha e modo teste selecionados
    contagem = tipo_contagem.get()
    planilha = tipo_planilha.get()
    teste = modo_teste.get()

    # Confirmação
    modo_msg = "\n🧪 Modo Teste: ATIVADO (imagens alternativas)" if teste else ""
    resposta = messagebox.askyesno(
        "Confirmar Início",
        f"Inventário: {inventario}\n"
        f"Robô: {robo_id}\n"
        f"Planilha: {planilha.upper()}\n"
        f"Tipo: {contagem.title()} Contagem{modo_msg}\n\n"
        "Certifique-se de que:\n\n"
        "✓ O sistema está aberto\n"
        "✓ Você está na tela correta\n"
        "✓ A configuração está correta\n\n"
        "Deseja iniciar o RPA?"
    )

    if not resposta:
        return

    # Salvar parâmetros no estado
    estado["inventario"] = inventario
    estado["robo_id"] = robo_id
    estado["tipo_contagem"] = contagem
    estado["tipo_planilha"] = planilha
    estado["modo_teste"] = teste

    # Minimizar janela
    app.iconify()

    # Atualizar estado
    estado["executando"] = True
    btn_iniciar.config(state='disabled')
    btn_parar.config(state='normal')
    status_label.config(text="Status: Rodando", fg="green")
    set_title_running(True)

    # Limpar log
    log_text.config(state='normal')
    log_text.delete(1.0, 'end')
    log_text.config(state='disabled')

    # Iniciar thread do RPA
    estado["thread_rpa"] = threading.Thread(target=rpa_worker, daemon=True)
    estado["thread_rpa"].start()

    log_interface("▶️ Iniciando RPA Inventário...")

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
    ajuda_window.title("Ajuda - RPA Inventário")
    ajuda_window.geometry("700x600")
    ajuda_window.resizable(False, False)

    # Texto de ajuda
    ajuda_text = scrolledtext.ScrolledText(ajuda_window, wrap=tk.WORD, padx=10, pady=10, font=("Arial", 9))
    ajuda_text.pack(fill=tk.BOTH, expand=True)

    help_content = """
🤖 RPA INVENTÁRIO - AJUDA

📋 FUNCIONALIDADES:
• Automação de processos de inventário
• Utiliza Playwright para interação web
• Interface gráfica intuitiva
• Logs detalhados de execução
• Parada de emergência (ESC)

🚀 COMO USAR:

1. PREPARAÇÃO:
   - Configure o arquivo config.json com as coordenadas necessárias
   - Certifique-se de ter acesso à internet
   - Verifique as credenciais de acesso

2. EXECUÇÃO:
   - Clique em "🎯 Iniciar RPA"
   - O RPA executará todas as etapas automaticamente
   - Acompanhe o progresso pelo log

3. PARADA:
   - Pressione ESC a qualquer momento
   - Ou clique em "⏹️ Parar RPA"

🔒 SEGURANÇA:
• Pressione ESC para parar imediatamente
• Botão "⏹️ Parar RPA" para interrupção manual
• Logs salvos automaticamente

🔧 TROUBLESHOOTING:
• Se elementos não forem encontrados: Verifique config.json
• Para problemas de conexão: Verifique internet
• Se o navegador não abrir: Reinstale Playwright

📞 INFORMAÇÕES:
• Versão: 1.0
• Data: Dezembro 2025
• Desenvolvido com Playwright
    """

    ajuda_text.insert(1.0, help_content)
    ajuda_text.config(state='disabled')

    # Botão fechar
    tk.Button(ajuda_window, text="Fechar", command=ajuda_window.destroy, font=("Arial", 10), bg="#2196F3", fg="white").pack(pady=10)

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Inventário v1.0")
app.geometry("850x700")
app.resizable(True, True)

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
    tk.Label(logo_frame, text="RPA INVENTÁRIO", font=("Arial", 14, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONFIGURAÇÃO (INVENTÁRIO E CONTAGEM) ──────────────────────────
config_frame = tk.Frame(app, bg="#f0f0f0", relief=tk.RAISED, bd=2)
config_frame.pack(pady=10, padx=20, fill=tk.X)

# Label do frame
tk.Label(config_frame, text="Configuração do Inventário", font=("Arial", 10, "bold"), bg="#f0f0f0").pack(pady=(5, 10))

# Campo de inventário
inventario_row = tk.Frame(config_frame, bg="#f0f0f0")
inventario_row.pack(pady=5)

tk.Label(inventario_row, text="Inventário:", font=("Arial", 9), bg="#f0f0f0", width=12, anchor="e").pack(side="left", padx=(10, 5))
entry_inventario = tk.Entry(inventario_row, font=("Arial", 10), width=20)
entry_inventario.pack(side="left", padx=5)

tk.Label(inventario_row, text="Robô:", font=("Arial", 9), bg="#f0f0f0").pack(side="left", padx=(15, 5))
entry_robo_id = tk.Entry(inventario_row, font=("Arial", 10, "bold"), width=15, state='readonly', readonlybackground="#e0e0e0")
entry_robo_id.pack(side="left", padx=5)
# Inserir nome do computador
entry_robo_id.config(state='normal')
entry_robo_id.delete(0, tk.END)
entry_robo_id.insert(0, NOME_COMPUTADOR)
entry_robo_id.config(state='readonly')

# Radio buttons para tipo de planilha (BC1/BC2)
planilha_row = tk.Frame(config_frame, bg="#f0f0f0")
planilha_row.pack(pady=5)

tk.Label(planilha_row, text="Planilha:", font=("Arial", 9), bg="#f0f0f0", width=12, anchor="e").pack(side="left", padx=(10, 5))

tipo_planilha = tk.StringVar(value="bc1")  # Valor padrão

rb_bc1 = tk.Radiobutton(
    planilha_row,
    text="BC1",
    variable=tipo_planilha,
    value="bc1",
    font=("Arial", 9),
    bg="#f0f0f0"
)
rb_bc1.pack(side="left", padx=10)

rb_bc2 = tk.Radiobutton(
    planilha_row,
    text="BC2",
    variable=tipo_planilha,
    value="bc2",
    font=("Arial", 9),
    bg="#f0f0f0"
)
rb_bc2.pack(side="left", padx=10)

# Radio buttons para tipo de contagem
contagem_row = tk.Frame(config_frame, bg="#f0f0f0")
contagem_row.pack(pady=5)

tk.Label(contagem_row, text="Tipo Contagem:", font=("Arial", 9), bg="#f0f0f0", width=12, anchor="e").pack(side="left", padx=(10, 5))

tipo_contagem = tk.StringVar(value="primeira")  # Valor padrão

rb_primeira = tk.Radiobutton(
    contagem_row,
    text="Primeira Contagem",
    variable=tipo_contagem,
    value="primeira",
    font=("Arial", 9),
    bg="#f0f0f0"
)
rb_primeira.pack(side="left", padx=10)

rb_segunda = tk.Radiobutton(
    contagem_row,
    text="Segunda Contagem",
    variable=tipo_contagem,
    value="segunda",
    font=("Arial", 9),
    bg="#f0f0f0"
)
rb_segunda.pack(side="left", padx=10)

# Checkbox para Modo Teste
teste_row = tk.Frame(config_frame, bg="#f0f0f0")
teste_row.pack(pady=5)

tk.Label(teste_row, text="", font=("Arial", 9), bg="#f0f0f0", width=12, anchor="e").pack(side="left", padx=(10, 5))

modo_teste = tk.BooleanVar(value=False)  # Desativado por padrão

cb_modo_teste = tk.Checkbutton(
    teste_row,
    text="🧪 Modo Teste (usar imagens alternativas)",
    variable=modo_teste,
    font=("Arial", 9),
    bg="#f0f0f0"
)
cb_modo_teste.pack(side="left", padx=10)

# Espaço após configuração
tk.Label(config_frame, text="", bg="#f0f0f0").pack(pady=2)

# ─── ÁREA DE CONTROLES (REORGANIZADA) ──────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=5)

# Botões principais e utilitários na mesma linha
btn_iniciar = tk.Button(
    controls_frame,
    text="🎯 Iniciar RPA",
    command=iniciar_rpa,
    font=("Arial", 10, "bold"),
    bg="#2196F3",
    fg="white",
    padx=10,
    pady=6,
    width=14
)
btn_iniciar.pack(side="left", padx=3)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar RPA",
    command=parar_rpa,
    font=("Arial", 10, "bold"),
    bg="#f44336",
    fg="white",
    padx=10,
    pady=6,
    width=14,
    state='disabled'
)
btn_parar.pack(side="left", padx=3)

tk.Button(
    controls_frame,
    text="❓ Ajuda",
    command=mostrar_ajuda,
    font=("Arial", 9),
    padx=8,
    pady=6,
    width=10
).pack(side="left", padx=3)

# ─── STATUS ─────────────────────────────────────────────────────────────────
status_frame = tk.Frame(app)
status_frame.pack(pady=4)

status_label = tk.Label(
    status_frame,
    text="Status: Aguardando",
    font=("Arial", 10, "bold"),
    fg="orange"
)
status_label.pack()

# ─── DIVISOR ENTRE SEÇÕES ───────────────────────────────────────────────────
separator1 = ttk.Separator(app, orient='horizontal')
separator1.pack(fill='x', padx=20, pady=3)

# ─── ÁREA DE LOG (AUMENTADA) ───────────────────────────────────────────────
log_frame = tk.Frame(app)
log_frame.pack(pady=3, padx=15, fill=tk.BOTH, expand=True)

tk.Label(log_frame, text="📋 Log de Execução:", font=("Arial", 9, "bold")).pack(anchor="w")

# Text widget com scrollbar (MAIOR)
log_text = scrolledtext.ScrolledText(
    log_frame,
    height=30,
    width=120,
    wrap=tk.WORD,
    state='disabled',
    font=("Consolas", 9),
    bg="#f8f8f8"
)
log_text.pack(fill=tk.BOTH, expand=True, pady=(3, 0))

# ─── INICIALIZAÇÃO ──────────────────────────────────────────────────────────
# Ajusta o título inicial
set_title_running(False)

# Log inicial
log_interface("🤖 RPA Inventário v1.0 carregado")
log_interface("✅ Sistema pronto para iniciar")
log_interface("📖 Clique em 'Ajuda' para instruções detalhadas")
log_interface("")
log_interface("Clique em '🎯 Iniciar RPA' para começar a automação")

# Interceptar fechamento da janela
def on_closing():
    """Fecha a aplicação e mata todos os processos"""
    if estado["executando"]:
        resposta = messagebox.askyesno(
            "Confirmar Saída",
            "RPA está em execução. Deseja realmente sair?\n\n"
            "Isso interromperá a automação."
        )
        if not resposta:
            return

        # Parar RPA se estiver rodando
        log_interface("⏸️ Parando RPA...")
        parar_rpa()

        # Aguardar thread terminar (máximo 3 segundos)
        if estado.get("thread_rpa") and estado["thread_rpa"].is_alive():
            log_interface("⏳ Aguardando thread RPA terminar...")
            estado["thread_rpa"].join(timeout=3)

    # Limpar hooks do keyboard SEMPRE
    try:
        import keyboard
        keyboard.unhook_all()
        log_interface("🧹 Keyboard hooks limpos")
    except Exception as e:
        print(f"Erro ao limpar keyboard: {e}")

    # Limpar PyAutoGUI failsafe
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
    except:
        pass

    log_interface("👋 Encerrando aplicação...")

    # Destruir janela
    try:
        app.quit()
        app.destroy()
    except:
        pass

    # FORÇAR encerramento do processo Python
    # Isso garante que o processo morra completamente
    import os
    os._exit(0)

app.protocol("WM_DELETE_WINDOW", on_closing)

# ─── EXECUÇÃO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.mainloop()
