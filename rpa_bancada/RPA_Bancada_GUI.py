# -*- coding: utf-8 -*-
import threading
import time
import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import subprocess

# Importar o módulo principal do RPA
import main

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Estado global do RPA
estado = {"executando": False, "thread_rpa": None}

# ─── HELPERS DE UI ──────────────────────────────────────────────────────────
def set_title_running(is_running: bool, extra: str = ""):
    """Atualiza o título da janela conforme o status"""
    base = "RPA Bancada Oracle"
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

        log_interface("🚀 RPA iniciado - automatizando Oracle Applications...")
        log_interface("⚠️ FAILSAFE ativo: mova o mouse para o canto superior esquerdo para parar")

        # Chama a função main do RPA original com execução única
        main.main(single_run=False)  # Loop infinito

        # Quando terminar, mostrar notificação
        log_interface("=" * 70)
        log_interface("✅ RPA FINALIZADO AUTOMATICAMENTE")
        log_interface("=" * 70)
        app.after(0, lambda: messagebox.showinfo("RPA Concluído", "Automação finalizada!\n\nClique em 'Iniciar RPA' novamente para nova execução."))

    except KeyboardInterrupt:
        log_interface("🛑 RPA interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        log_interface(f"❌ Erro no RPA: {e}")
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

    # Confirmação
    resposta = messagebox.askyesno(
        "Confirmar Início",
        "Certifique-se de que:\n\n"
        "✓ Oracle Applications está aberto\n"
        "✓ Você está na tela da Bancada de Material\n"
        "✓ A resolução está em 1440x900 (recomendado)\n\n"
        "Deseja iniciar o RPA?"
    )

    if not resposta:
        return

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

    log_interface("▶️ Iniciando RPA...")

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

def abrir_pasta_out():
    """Abre a pasta de saída onde são salvos os arquivos Excel"""
    try:
        pasta_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
        os.makedirs(pasta_out, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(pasta_out)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", pasta_out])
        else:
            subprocess.Popen(["xdg-open", pasta_out])

        log_interface(f"📂 Pasta aberta: {pasta_out}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def mostrar_ajuda():
    """Mostra janela de ajuda"""
    ajuda_window = tk.Toplevel(app)
    ajuda_window.title("Ajuda - RPA Bancada Oracle")
    ajuda_window.geometry("600x500")
    ajuda_window.resizable(False, False)

    # Texto de ajuda
    ajuda_text = tk.Text(ajuda_window, wrap=tk.WORD, padx=10, pady=10)
    ajuda_text.pack(fill=tk.BOTH, expand=True)

    help_content = """
🤖 RPA BANCADA ORACLE - AJUDA

📋 FUNCIONALIDADES:
• Automação completa do Oracle Applications
• Extração de dados da Bancada de Material
• Backup automático em Excel (pasta 'out/')
• Sincronização com Google Sheets
• Sistema Keep-Awake (evita bloqueio por inatividade)

🚀 COMO USAR:
1. Abra o Oracle Applications
2. Navegue até a Bancada de Material
3. Ajuste a resolução para 1440x900 (recomendado)
4. Clique em "Iniciar RPA"
5. O programa automaticamente:
   - Clicará em "Detalhado"
   - Clicará em "Localizar"
   - Selecionará "Copiar Todas as Linhas"
   - Processará os dados
   - Salvará em Excel e Google Sheets

🔒 SEGURANÇA:
• FAILSAFE: Mova o mouse para o canto superior esquerdo para parar
• Botão "Parar RPA" para interrupção manual
• Dados sempre salvos localmente como backup

📊 DADOS EXTRAÍDOS:
As 8 colunas principais são enviadas para Google Sheets:
• ORG. (Organização)
• SUB. (Subinventário)
• ENDEREÇO (Localização)
• ITEM (Código do Item)
• DESCRIÇÃO ITEM (Descrição)
• REV. (Revisão)
• UDM PRINCIPAL (Unidade de Medida)
• EM ESTOQUE (Quantidade)

⚙️ CONFIGURAÇÕES:
• Planilha Google Sheets: Configurada automaticamente
• Credenciais: CredenciaisOracle.json
• Primeira execução pode pedir autorização no navegador

🔧 TROUBLESHOOTING:
• Se elementos não forem encontrados: Verifique resolução da tela
• Se falhar Google Sheets: Dados ainda são salvos em Excel local
• Para problemas de permissão: Execute como Administrador

📞 SUPORTE:
• Versão: 1.0
• Data: 27/09/2025
• Desenvolvido para automação da Bancada de Material Oracle
    """

    ajuda_text.insert(1.0, help_content)
    ajuda_text.config(state='disabled')

    # Botão fechar
    tk.Button(ajuda_window, text="Fechar", command=ajuda_window.destroy).pack(pady=10)

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Bancada Oracle")
app.geometry("550x650")
app.resizable(False, False)

# Ícone da janela
try:
    app.iconphoto(True, ImageTk.PhotoImage(file=os.path.join(base_path, "Topo.png")))
except Exception as e:
    print(f"Erro ao definir ícone: {e}")

# ─── ÁREA DOS LOGOS ─────────────────────────────────────────────────────────
try:
    logo_frame = tk.Frame(app, bg="#f7f7f7")
    logo_frame.pack(pady=(20, 15), fill=tk.X)

    # Logo Genesys
    logo1_img = Image.open(os.path.join(base_path, "Logo.png")).resize((150, 90))
    logo1_tk = ImageTk.PhotoImage(logo1_img)

    # Logo Tecumseh
    logo2_img = Image.open(os.path.join(base_path, "Tecumseh.png")).resize((90, 70))
    logo2_tk = ImageTk.PhotoImage(logo2_img)

    # Container centralizado para os logos
    logos_container = tk.Frame(logo_frame, bg="#f7f7f7")
    logos_container.pack()

    tk.Label(logos_container, image=logo1_tk, bg="#f7f7f7").pack(side="left", padx=15)
    tk.Label(logos_container, image=logo2_tk, bg="#f7f7f7").pack(side="left", padx=15)

except Exception as e:
    print(f"❌ Erro ao carregar logos: {e}")
    # Frame vazio se logos falharem
    logo_frame = tk.Frame(app, height=100, bg="#f7f7f7")
    logo_frame.pack(pady=(20, 15), fill=tk.X)
    tk.Label(logo_frame, text="RPA BANCADA ORACLE", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONTROLES ──────────────────────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=10)

# Botões principais
btn_iniciar = tk.Button(
    controls_frame,
    text="🚀 Iniciar RPA",
    command=iniciar_rpa,
    font=("Arial", 12, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    width=15
)
btn_iniciar.pack(side="left", padx=10)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar RPA",
    command=parar_rpa,
    font=("Arial", 12, "bold"),
    bg="#f44336",
    fg="white",
    padx=20,
    pady=10,
    width=15,
    state='disabled'
)
btn_parar.pack(side="left", padx=10)

# ─── ÁREA DE UTILITÁRIOS ────────────────────────────────────────────────────
utils_frame = tk.Frame(app)
utils_frame.pack(pady=10)

tk.Button(
    utils_frame,
    text="📂 Abrir Pasta Excel",
    command=abrir_pasta_out,
    font=("Arial", 10),
    padx=15,
    pady=5
).pack(side="left", padx=5)

tk.Button(
    utils_frame,
    text="❓ Ajuda",
    command=mostrar_ajuda,
    font=("Arial", 10),
    padx=15,
    pady=5
).pack(side="left", padx=5)

# ─── STATUS ─────────────────────────────────────────────────────────────────
status_frame = tk.Frame(app)
status_frame.pack(pady=10)

status_label = tk.Label(
    status_frame,
    text="Status: Aguardando",
    font=("Arial", 12, "bold"),
    fg="orange"
)
status_label.pack()

# ─── ÁREA DE LOG ────────────────────────────────────────────────────────────
log_frame = tk.Frame(app)
log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

tk.Label(log_frame, text="📋 Log de Execução:", font=("Arial", 10, "bold")).pack(anchor="w")

# Text widget com scrollbar
log_text = scrolledtext.ScrolledText(
    log_frame,
    height=20,
    width=70,
    wrap=tk.WORD,
    state='disabled',
    font=("Consolas", 9),
    bg="#f8f8f8"
)
log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

# ─── INICIALIZAÇÃO ──────────────────────────────────────────────────────────
# Ajusta o título inicial
set_title_running(False)

# Log inicial
log_interface("🤖 RPA Bancada Oracle carregado")
log_interface("✅ Sistema pronto para iniciar")
log_interface("📖 Clique em 'Ajuda' para instruções detalhadas")

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

    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# ─── EXECUÇÃO ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.mainloop()