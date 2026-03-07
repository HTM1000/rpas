#!/usr/bin/env python3
"""Script para otimizar delays e implementar melhorias no RPA Ciclo"""

def aplicar_otimizacoes():
    # Ler arquivo original
    with open("essential/main_ciclo.py", "r", encoding="utf-8") as f:
        conteudo = f.read()

    print("Aplicando otimizacoes...")

    # 1. Reduzir delay de validacao OCR (linha ~2515-2516)
    conteudo = conteudo.replace(
        'gui_log("[VALIDADOR] Aguardando 3 segundos para campos estabilizarem...")\n                        time.sleep(3)  # Timeout maior para dar tempo da tela estabilizar',
        'gui_log("[VALIDADOR] Aguardando 1 segundo para campos estabilizarem...")\n                        time.sleep(1)  # Reduzido para acelerar validacao'
    )
    print("OK 1. Delay de validacao OCR reduzido (3s -> 1s)")

    # 2. Reduzir delay apos F6 na validacao (linha ~2620-2621)
    conteudo = conteudo.replace(
        'gui_log("[VALIDADOR] Aguardando 3 segundos para formulário limpar...")\n                                        time.sleep(3)  # Aguardar formulário limpar',
        'gui_log("[VALIDADOR] Aguardando 1.5 segundos para formulario limpar...")\n                                        time.sleep(1.5)  # Aguardar formulario limpar'
    )
    print("OK 2. Delay apos F6 (validacao) reduzido (3s -> 1.5s)")

    # 3. Reduzir delays apos Ctrl+S (linhas ~2788-2791)
    conteudo = conteudo.replace(
        'gui_log("[SAVE] Aguardando 1 segundo...")\n                    time.sleep(1)\n                    gui_log("[SAVE] Aguardando mais 0.5 segundos...")\n                    time.sleep(0.5)',
        'gui_log("[SAVE] Aguardando 0.5 segundos...")\n                    time.sleep(0.5)'
    )
    print("OK 3. Delays apos Ctrl+S reduzidos (1.5s -> 0.5s)")

    # 4. Reduzir delay antes de F6 no salvamento (linha ~2857)
    conteudo = conteudo.replace(
        'gui_log(f"[SAVE] >> Tentativa {tentativa+1}/3: Pressionando F6...")\n                                        time.sleep(0.3)  # Pequeno delay antes de pressionar',
        'gui_log(f"[SAVE] >> Tentativa {tentativa+1}/3: Pressionando F6...")\n                                        time.sleep(0.1)  # Pequeno delay antes de pressionar'
    )
    print("OK 4. Delay antes de F6 (save) reduzido (0.3s -> 0.1s)")

    # 5. Reduzir delay apos F6 no salvamento (linha ~2859)
    conteudo = conteudo.replace(
        'time.sleep(0.5)  # Aguardar tecla ser processada\n                                            gui_log(f"[SAVE] << F6 pressionado (tentativa {tentativa+1})")',
        'time.sleep(0.2)  # Aguardar tecla ser processada\n                                            gui_log(f"[SAVE] << F6 pressionado (tentativa {tentativa+1})")'
    )
    print("OK 5. Delay apos F6 (save) reduzido (0.5s -> 0.2s)")

    # 6. Reduzir delay de aguardar formulario limpar apos F6 no save (linha ~2885)
    conteudo = conteudo.replace(
        'gui_log("[SAVE] Aguardando 3 segundos para formulário limpar...")\n                                            time.sleep(3)',
        'gui_log("[SAVE] Aguardando 1.5 segundos para formulario limpar...")\n                                            time.sleep(1.5)'
    )
    print("OK 6. Delay apos F6 final (save) reduzido (3s -> 1.5s)")

    # 7. Reduzir delay antes de F6 na validacao (linha ~2593)
    conteudo = conteudo.replace(
        'gui_log(f"[VALIDADOR] >> Tentativa {tentativa+1}/3: Pressionando F6...")\n                                            time.sleep(0.3)  # Pequeno delay antes de pressionar',
        'gui_log(f"[VALIDADOR] >> Tentativa {tentativa+1}/3: Pressionando F6...")\n                                            time.sleep(0.1)  # Pequeno delay antes de pressionar'
    )
    print("OK 7. Delay antes de F6 (validacao) reduzido (0.3s -> 0.1s)")

    # 8. Reduzir delay apos F6 na validacao (linha ~2595)
    conteudo = conteudo.replace(
        'time.sleep(0.5)  # Aguardar tecla ser processada\n                                            gui_log(f"[VALIDADOR] << F6 pressionado (tentativa {tentativa+1})")',
        'time.sleep(0.2)  # Aguardar tecla ser processada\n                                            gui_log(f"[VALIDADOR] << F6 pressionado (tentativa {tentativa+1})")'
    )
    print("OK 8. Delay apos F6 (validacao) reduzido (0.5s -> 0.2s)")

    # Salvar arquivo modificado
    with open("essential/main_ciclo.py", "w", encoding="utf-8") as f:
        f.write(conteudo)

    print("\nOtimizacoes aplicadas com sucesso!")
    print("\nResumo das melhorias:")
    print("   - Validacao OCR: 3s -> 1s (reducao de 66%)")
    print("   - Delays apos Ctrl+S: 1.5s -> 0.5s (reducao de 66%)")
    print("   - Limpeza de formulario: 3s -> 1.5s (reducao de 50%)")
    print("   - Delays de F6: 0.8s -> 0.3s (reducao de 62%)")
    print("\nGanho estimado por item: ~4-5 segundos")

if __name__ == "__main__":
    aplicar_otimizacoes()
