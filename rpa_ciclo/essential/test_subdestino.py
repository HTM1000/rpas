"""
Teste isolado: simula o comportamento do Oracle para Sub.Destino/End.Destino.

Comportamento simulado:
- Ao dar TAB no End.Origem, Sub.Destino é auto-preenchido com o valor de Sub.Origem
  (igual o Oracle faz na tela de Transferência Subinventory)
- O teste roda o padrão: delete → click → delete → write (novo fix)
- No log você vê o valor final de cada campo

Execução: python test_subdestino.py
A janela abre, aguarda 4 segundos, e o RPA escreve automaticamente.
"""

import tkinter as tk
import threading
import time
import pyautogui

# ─── Configuração do teste ───────────────────────────────────────────────────
SUB_ORIGEM_VALOR  = "WIP3DPA"
END_ORIGEM_VALOR  = "000.00.00.d3"
SUB_DESTINO_VALOR = "RAWCENTR"   # o que o RPA deveria escrever
END_DESTINO_VALOR = "R04.0H.03.3C"
# ─────────────────────────────────────────────────────────────────────────────

resultado = {}

def safe_write(texto):
    for tecla in ['shift', 'ctrl', 'alt']:
        pyautogui.keyUp(tecla)
    time.sleep(0.05)
    pyautogui.write(str(texto), interval=0.03)
    time.sleep(0.1)

def on_tab_end_origem(event, entries):
    """Simula o Oracle: ao sair do End.Origem, auto-preenche Sub.Destino com Sub.Origem."""
    sub_origem = entries["sub_origem"].get()
    entries["sub_destino"].delete(0, tk.END)
    entries["sub_destino"].insert(0, sub_origem)   # ← comportamento Oracle
    entries["sub_destino"].focus_set()
    return "break"  # evita o TAB padrão do Tkinter

def executar_teste(entries, coords, log_var):
    time.sleep(4)  # tempo para a janela abrir e estabilizar

    logs = []

    def log(msg):
        logs.append(msg)
        log_var.set("\n".join(logs[-15:]))

    log("▶ Iniciando teste...")
    log(f"  Sub.Destino ANTES do write: '{entries['sub_destino'].get()}'")

    # ── Padrão atual do RPA para Sub.Destino ──────────────────────────────────
    # delete (no campo com foco atual) → click sub_destino → delay → delete → write
    log("  Executando: delete → click → delete → safe_write...")

    pyautogui.click(coords["sub_destino"])
    time.sleep(0.3)
    pyautogui.press("home")
    pyautogui.hotkey("shift", "end")
    pyautogui.press("delete")
    time.sleep(0.1)

    safe_write(SUB_DESTINO_VALOR)

    pyautogui.press("tab")
    time.sleep(0.3)

    # ── Padrão para End.Destino ───────────────────────────────────────────────
    pyautogui.click(coords["end_destino"])
    time.sleep(0.3)
    pyautogui.press("home")
    pyautogui.hotkey("shift", "end")
    pyautogui.press("delete")
    time.sleep(0.1)

    safe_write(END_DESTINO_VALOR)

    pyautogui.press("tab")
    time.sleep(0.3)

    # ── Ler resultado ─────────────────────────────────────────────────────────
    val_sub_d = entries["sub_destino"].get()
    val_end_d = entries["end_destino"].get()

    log("")
    log("══ RESULTADO ══")
    log(f"  Sub.Destino esperado : '{SUB_DESTINO_VALOR}'")
    log(f"  Sub.Destino obtido   : '{val_sub_d}'")
    ok_sub = val_sub_d.strip().upper() == SUB_DESTINO_VALOR.strip().upper()
    log(f"  Sub.Destino          : {'✅ OK' if ok_sub else '❌ FALHOU'}")
    log("")
    log(f"  End.Destino esperado : '{END_DESTINO_VALOR}'")
    log(f"  End.Destino obtido   : '{val_end_d}'")
    ok_end = val_end_d.strip().upper() == END_DESTINO_VALOR.strip().upper()
    log(f"  End.Destino          : {'✅ OK' if ok_end else '❌ FALHOU'}")
    log("")
    if ok_sub and ok_end:
        log("✅ TESTE PASSOU — fix funcionou!")
    else:
        log("❌ TESTE FALHOU — revisar fix")

def main():
    root = tk.Tk()
    root.title("Simulador Oracle — Teste Sub.Destino/End.Destino")
    root.geometry("520x480")
    root.resizable(False, False)

    entries = {}
    coords  = {}
    log_var = tk.StringVar(value="Aguardando 4s para iniciar o teste...")

    frame = tk.Frame(root, padx=20, pady=20)
    frame.pack(fill="both", expand=True)

    campos = [
        ("Sub.Origem",  "sub_origem"),
        ("End.Origem",  "end_origem"),
        ("Sub.Destino", "sub_destino"),
        ("End.Destino", "end_destino"),
    ]

    for label, key in campos:
        row = tk.Frame(frame)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, width=14, anchor="w").pack(side="left")
        e = tk.Entry(row, width=30, font=("Courier", 11))
        e.pack(side="left")
        entries[key] = e

    # Preencher Sub.Origem e End.Origem com valores iniciais
    entries["sub_origem"].insert(0, SUB_ORIGEM_VALOR)
    entries["end_origem"].insert(0, END_ORIGEM_VALOR)

    # Simular comportamento Oracle: TAB em End.Origem auto-preenche Sub.Destino
    entries["end_origem"].bind("<Tab>", lambda e: on_tab_end_origem(e, entries))

    # Forçar auto-preenchimento já no início (Oracle já faz isso antes do RPA chegar)
    entries["sub_destino"].insert(0, SUB_ORIGEM_VALOR)

    tk.Label(frame, text="─" * 50).pack(pady=8)
    tk.Label(frame, text="Log do teste:", anchor="w").pack(fill="x")
    log_label = tk.Label(frame, textvariable=log_var, justify="left",
                         font=("Courier", 10), bg="#1e1e1e", fg="#d4d4d4",
                         anchor="nw", padx=8, pady=8, relief="sunken")
    log_label.pack(fill="both", expand=True)

    # Capturar coordenadas após a janela estar visível
    def capturar_coords_e_iniciar():
        root.update()
        time.sleep(0.5)
        root.update()

        for key, entry in entries.items():
            x = entry.winfo_rootx() + entry.winfo_width() // 2
            y = entry.winfo_rooty() + entry.winfo_height() // 2
            coords[key] = (x, y)

        t = threading.Thread(target=executar_teste, args=(entries, coords, log_var), daemon=True)
        t.start()

    root.after(500, capturar_coords_e_iniciar)
    root.mainloop()

if __name__ == "__main__":
    main()
