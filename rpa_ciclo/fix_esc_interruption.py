#!/usr/bin/env python3
"""Script para corrigir funcionalidade ESC e implementar status 'Interrompido'"""

def aplicar_correcoes():
    # Ler arquivo original
    with open("essential/main_ciclo.py", "r", encoding="utf-8") as f:
        conteudo = f.read()

    print("Aplicando correcoes de interrupcao ESC...")

    # 1. Modificar verificação _rpa_running no início do loop de itens
    # Trocar simples "return False" por marcar item como interrompido
    old_code_1 = """            # Processar cada linha
            for i, linha in linhas_processar:
                if not _rpa_running:
                    return False

                item = linha.get("Item", "").strip()"""

    new_code_1 = """            # Processar cada linha
            for i, linha in linhas_processar:
                if not _rpa_running:
                    gui_log("⚠️ [INTERRUPÇÃO] RPA foi interrompido. Encerrando processamento...")
                    return False

                item = linha.get("Item", "").strip()"""

    conteudo = conteudo.replace(old_code_1, new_code_1)
    print("OK 1. Adicionada mensagem de interrupcao no inicio do loop")

    # 2. Adicionar verificação após preencher cada campo importante
    # Após preencher Item (linha ~2291)
    old_code_2 = """                    gui_log(f"[ITEM] Aguardando 1 segundo...")
                    time.sleep(1)
                    gui_log(f"[ITEM] ✅ Item preenchido")

                    # ═══════════════════════════════════════════════════════════════
                    # VERIFICAR ERRO DE PRODUTO (LOGO APÓS ITEM) - IGUAL RPA_ORACLE
                    # ═══════════════════════════════════════════════════════════════"""

    new_code_2 = """                    gui_log(f"[ITEM] Aguardando 1 segundo...")
                    time.sleep(1)
                    gui_log(f"[ITEM] ✅ Item preenchido")

                    # Verificar se foi interrompido
                    if not _rpa_running:
                        gui_log("⚠️ [INTERRUPÇÃO] RPA interrompido após preencher Item")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Interrompido - Refazer"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Interrompido - Refazer'")
                        except:
                            pass
                        return False

                    # ═══════════════════════════════════════════════════════════════
                    # VERIFICAR ERRO DE PRODUTO (LOGO APÓS ITEM) - IGUAL RPA_ORACLE
                    # ═══════════════════════════════════════════════════════════════"""

    conteudo = conteudo.replace(old_code_2, new_code_2)
    print("OK 2. Adicionada verificacao apos preencher Item")

    # 3. Adicionar verificação antes de salvar (Ctrl+S)
    old_code_3 = """                    gui_log("[SAVE] Iniciando salvamento com Ctrl+S...")
                    gui_log("[SAVE] >> Pressionando CTRL+S...")
                    pyautogui.hotkey("ctrl", "s")"""

    new_code_3 = """                    # Verificar se foi interrompido antes de salvar
                    if not _rpa_running:
                        gui_log("⚠️ [INTERRUPÇÃO] RPA interrompido antes de Ctrl+S")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Interrompido - Refazer"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Interrompido - Refazer'")
                        except:
                            pass
                        return False

                    gui_log("[SAVE] Iniciando salvamento com Ctrl+S...")
                    gui_log("[SAVE] >> Pressionando CTRL+S...")
                    pyautogui.hotkey("ctrl", "s")"""

    conteudo = conteudo.replace(old_code_3, new_code_3)
    print("OK 3. Adicionada verificacao antes de Ctrl+S")

    # 4. Modificar adição ao cache para NÃO adicionar se status for "Interrompido"
    # (A verificação de _rpa_running já deve impedir isso, mas vamos garantir)
    old_code_4 = """                    # 💾 ADICIONAR AO CACHE **ANTES** DE Ctrl+S (CRÍTICO!)
                    # MUDANÇA CRÍTICA: Cache ANTES do Ctrl+S elimina gap de duplicação
                    # Se crash/queda entre Ctrl+S e adicionar cache, item seria duplicado
                    # Removido ao adicionar sistema de evidências v4.0
                    # Mantém-se aqui para compatibilidade
                    gui_log("💾 [CRÍTICO] Adicionando ao cache ANTES de Ctrl+S...")"""

    new_code_4 = """                    # 💾 ADICIONAR AO CACHE **ANTES** DE Ctrl+S (CRÍTICO!)
                    # MUDANÇA CRÍTICA: Cache ANTES do Ctrl+S elimina gap de duplicação
                    # Se crash/queda entre Ctrl+S e adicionar cache, item seria duplicado
                    # Removido ao adicionar sistema de evidências v4.0
                    # Mantém-se aqui para compatibilidade

                    # ⚠️ VERIFICAR SE FOI INTERROMPIDO - NÃO ADICIONAR AO CACHE SE SIM
                    if not _rpa_running:
                        gui_log("⚠️ [INTERRUPÇÃO] RPA interrompido - NÃO adicionando ao cache")
                        try:
                            service.spreadsheets().values().update(
                                spreadsheetId=SPREADSHEET_ID,
                                range=range_str,
                                valueInputOption="RAW",
                                body={"values": [["Interrompido - Refazer"]]}
                            ).execute()
                            gui_log("✅ Status atualizado: 'Interrompido - Refazer'")
                        except:
                            pass
                        return False

                    gui_log("💾 [CRÍTICO] Adicionando ao cache ANTES de Ctrl+S...")"""

    conteudo = conteudo.replace(old_code_4, new_code_4)
    print("OK 4. Protecao contra adicao ao cache quando interrompido")

    # Salvar arquivo modificado
    with open("essential/main_ciclo.py", "w", encoding="utf-8") as f:
        f.write(conteudo)

    print("\nCorrecoes aplicadas com sucesso!")
    print("\nResumo:")
    print("  - ESC agora atualiza Google Sheets com 'Interrompido - Refazer'")
    print("  - Item interrompido NAO e adicionado ao cache")
    print("  - Item pode ser reprocessado no proximo ciclo")
    print("  - Verificacoes em 4 pontos criticos do processamento")

if __name__ == "__main__":
    aplicar_correcoes()
