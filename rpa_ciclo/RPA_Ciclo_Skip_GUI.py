# -*- coding: utf-8 -*-
"""
RPA CICLO - Interface Gráfica
Sistema de automação de ciclo completo Oracle
"""

import threading
import time
import os
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import subprocess

# Importar o módulo principal do RPA
import main_ciclo_skip as main_ciclo

# Diretório base compatível com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

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

# ─── CONTROLE DO RPA ────────────────────────────────────────────────────────
def rpa_worker():
    """Thread worker que executa o RPA principal"""
    try:
        # Configurar callback de log para a GUI
        main_ciclo.set_gui_log_callback(log_interface)

        modo = "CONTÍNUO (repete a cada 30 min)" if estado["modo_continuo"] else "ÚNICA EXECUÇÃO"
        log_interface(f"🚀 RPA iniciado - Modo: {modo}")
        log_interface("⚠️ FAILSAFE ativo: mova o mouse para o canto superior esquerdo para parar")

        # Chama a função main do RPA
        main_ciclo.main(modo_continuo=estado["modo_continuo"])

        # Quando terminar, mostrar notificação
        log_interface("=" * 70)
        log_interface("✅ RPA FINALIZADO")
        log_interface("=" * 70)

        mensagem = "Automação finalizada!\n\n"
        if estado["modo_continuo"]:
            mensagem += "Modo contínuo foi interrompido.\nClique em 'Iniciar RPA' para nova execução."
        else:
            mensagem += "Ciclo único concluído.\nClique em 'Iniciar RPA' para executar novamente."

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

    modo_str = "contínuo (repete a cada 30 min)" if modo_continuo else "execução única"

    # Confirmação
    resposta = messagebox.askyesno(
        "Confirmar Início",
        f"Modo: {modo_str.upper()}\n\n"
        "Certifique-se de que:\n\n"
        "✓ Oracle Applications está aberto\n"
        "✓ Você está na tela inicial correta\n"
        "✓ RPA_Oracle e RPA_Bancada estão acessíveis\n\n"
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
    main_ciclo.stop_rpa()

    log_interface("🛑 Solicitando parada do RPA...")

    # Restaurar interface
    restaurar_app()

    # Atualizar interface
    atualizar_interface_parado()

def abrir_pasta_logs():
    """Abre a pasta onde fica o arquivo de log"""
    try:
        pasta_logs = os.path.dirname(os.path.abspath(__file__))
        os.makedirs(pasta_logs, exist_ok=True)

        if sys.platform.startswith("win"):
            os.startfile(pasta_logs)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", pasta_logs])
        else:
            subprocess.Popen(["xdg-open", pasta_logs])

        log_interface(f"📂 Pasta aberta: {pasta_logs}")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir pasta: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def abrir_google_sheets():
    """Abre a planilha do Google Sheets no navegador"""
    try:
        url = "https://docs.google.com/spreadsheets/d/14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk/edit"

        if sys.platform.startswith("win"):
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])

        log_interface("☁️ Google Sheets aberto no navegador")
    except Exception as e:
        log_interface(f"❌ Erro ao abrir Google Sheets: {e}")
        messagebox.showerror("Erro", f"Não foi possível abrir Google Sheets:\n{e}")

def mostrar_ajuda():
    """Mostra janela de ajuda"""
    ajuda_window = tk.Toplevel(app)
    ajuda_window.title("Ajuda - RPA Ciclo Automação")
    ajuda_window.geometry("650x550")
    ajuda_window.resizable(False, False)

    # Texto de ajuda
    ajuda_text = tk.Text(ajuda_window, wrap=tk.WORD, padx=10, pady=10)
    ajuda_text.pack(fill=tk.BOTH, expand=True)

    help_content = """
🤖 RPA CICLO AUTOMAÇÃO - AJUDA

📋 FUNCIONALIDADES:
• Automação completa do ciclo Oracle
• Transferência de Subinventário
• Execução automática do RPA_Oracle
• Execução automática do RPA_Bancada
• Registro de logs no Google Sheets
• Modo contínuo (repete a cada 30 minutos)

🚀 COMO USAR:

1. PREPARAÇÃO:
   - Abra o Oracle Applications
   - Navegue até a tela inicial
   - Certifique-se de que RPA_Oracle e RPA_Bancada estão acessíveis

2. EXECUÇÃO ÚNICA:
   - Clique em "🎯 Ciclo Único"
   - O RPA executará todas as etapas uma vez
   - Ao finalizar, você pode executar novamente

3. EXECUÇÃO CONTÍNUA:
   - Clique em "🔄 Modo Contínuo"
   - O RPA executará as etapas
   - Aguardará 30 minutos
   - Repetirá o processo automaticamente
   - Pressione "Parar" para interromper

🔒 SEGURANÇA:
• FAILSAFE: Mova o mouse para o canto superior esquerdo para parar
• Botão "Parar RPA" para interrupção manual
• Logs salvos automaticamente

📊 ETAPAS DO CICLO:
1. Transferência de Subinventário
2. Preenchimento do campo Tipo (SUB)
3. Seleção de Funcionário (Wallatas Moreira)
4. Confirmação
5. Execução do RPA_Oracle
6. Navegação pós-Oracle
7. Abertura da Bancada de Material
8. Execução do RPA_Bancada
9. Fechamento da Bancada
10. Aguardar 30 minutos (apenas no modo contínuo)

☁️ GOOGLE SHEETS:
• Todos os ciclos são registrados automaticamente
• Clique em "☁️ Google Sheets" para ver o histórico
• Informações registradas:
  - Data/Hora de Início e Fim
  - Número do Ciclo
  - Status (Sucesso/Falha/Pausado)
  - Tempo de Execução
  - Etapa que falhou (se houver)
  - Status do RPA Oracle
  - Status do RPA Bancada

⚙️ CONFIGURAÇÕES:
• Coordenadas: Edite o arquivo config.json
• Tempos de espera: Ajuste em config.json
• Credenciais: CredenciaisOracle.json
• Primeira execução pode pedir autorização no navegador

🔧 TROUBLESHOOTING:
• Se elementos não forem encontrados: Verifique resolução da tela
• Se falhar Google Sheets: Verifique credenciais e token.json
• Para problemas de coordenadas: Use mouse_position_helper.py
• Se RPA_Oracle/Bancada falharem: Verifique se os executáveis existem

🎯 DIFERENÇAS ENTRE MODOS:

CICLO ÚNICO:
✓ Executa uma vez
✓ Para automaticamente ao terminar
✓ Ideal para testes

MODO CONTÍNUO:
✓ Executa repetidamente
✓ Intervalo de 30 minutos entre ciclos
✓ Ideal para operação automática
✓ Requer parada manual

📞 INFORMAÇÕES:
• Versão: 2.0
• Data: Outubro 2025
• Desenvolvido para automação completa do ciclo Oracle
    """

    ajuda_text.insert(1.0, help_content)
    ajuda_text.config(state='disabled')

    # Botão fechar
    tk.Button(ajuda_window, text="Fechar", command=ajuda_window.destroy).pack(pady=10)

# ─── INTERFACE PRINCIPAL ────────────────────────────────────────────────────
app = tk.Tk()
app.title("RPA Ciclo Automação")
app.geometry("600x700")
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
    logo_frame.pack(pady=(20, 15), fill=tk.X)

    # Logo Genesys
    logo1_path = os.path.join(base_path, "Logo.png")
    if os.path.exists(logo1_path):
        logo1_img = Image.open(logo1_path).resize((150, 90))
        logo1_tk = ImageTk.PhotoImage(logo1_img)

        # Logo Tecumseh
        logo2_path = os.path.join(base_path, "Tecumseh.png")
        if os.path.exists(logo2_path):
            logo2_img = Image.open(logo2_path).resize((90, 70))
            logo2_tk = ImageTk.PhotoImage(logo2_img)

            # Container centralizado para os logos
            logos_container = tk.Frame(logo_frame, bg="#f7f7f7")
            logos_container.pack()

            tk.Label(logos_container, image=logo1_tk, bg="#f7f7f7").pack(side="left", padx=15)
            tk.Label(logos_container, image=logo2_tk, bg="#f7f7f7").pack(side="left", padx=15)
        else:
            raise FileNotFoundError("Logo Tecumseh não encontrado")
    else:
        raise FileNotFoundError("Logo Genesys não encontrado")

except Exception as e:
    print(f"❌ Erro ao carregar logos: {e}")
    # Frame vazio se logos falharem
    logo_frame = tk.Frame(app, height=100, bg="#f7f7f7")
    logo_frame.pack(pady=(20, 15), fill=tk.X)
    tk.Label(logo_frame, text="RPA CICLO AUTOMAÇÃO", font=("Arial", 16, "bold"), bg="#f7f7f7").pack()

# ─── ÁREA DE CONTROLES ──────────────────────────────────────────────────────
controls_frame = tk.Frame(app)
controls_frame.pack(pady=10)

# Botões principais
btn_iniciar_unico = tk.Button(
    controls_frame,
    text="🎯 Ciclo Único",
    command=lambda: iniciar_rpa(modo_continuo=False),
    font=("Arial", 11, "bold"),
    bg="#2196F3",
    fg="white",
    padx=15,
    pady=10,
    width=14
)
btn_iniciar_unico.pack(side="left", padx=5)

btn_iniciar_continuo = tk.Button(
    controls_frame,
    text="🔄 Modo Contínuo",
    command=lambda: iniciar_rpa(modo_continuo=True),
    font=("Arial", 11, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=15,
    pady=10,
    width=14
)
btn_iniciar_continuo.pack(side="left", padx=5)

btn_parar = tk.Button(
    controls_frame,
    text="⏹️ Parar RPA",
    command=parar_rpa,
    font=("Arial", 11, "bold"),
    bg="#f44336",
    fg="white",
    padx=15,
    pady=10,
    width=14,
    state='disabled'
)
btn_parar.pack(side="left", padx=5)

# ─── ÁREA DE UTILITÁRIOS ────────────────────────────────────────────────────
utils_frame = tk.Frame(app)
utils_frame.pack(pady=10)

tk.Button(
    utils_frame,
    text="📂 Abrir Logs",
    command=abrir_pasta_logs,
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
    height=22,
    width=75,
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
log_interface("🤖 RPA Ciclo Automação carregado")
log_interface("✅ Sistema pronto para iniciar")
log_interface("📖 Clique em 'Ajuda' para instruções detalhadas")
log_interface("")
log_interface("Escolha o modo de execução:")
log_interface("  🎯 Ciclo Único - Executa uma vez e para")
log_interface("  🔄 Modo Contínuo - Repete a cada 30 minutos")

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
