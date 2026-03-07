#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para adicionar modo loop infinito ao RPA Bancada
"""

import os

# Ler o arquivo original
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Adicionar import json
if 'import json' not in content:
    content = content.replace(
        'import os\n\nimport pyautogui',
        'import os\nimport json\n\nimport pyautogui'
    )

# 2. Adicionar carregamento de config após BASE
config_code = '''
# Carregar configurações do config.json
CONFIG = None
try:
    config_path = BASE / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)
    print(f"[OK] Configurações carregadas de {config_path}")
except Exception as e:
    print(f"[WARN] Erro ao carregar config.json: {e}")
    CONFIG = None

# ===== COORDENADAS (carregadas do config.json ou fixas) =====
if CONFIG:
    COORD_BANCADA_ABRIR = (CONFIG["coordenadas"]["tela_07_bancada_material"]["x"],
                           CONFIG["coordenadas"]["tela_07_bancada_material"]["y"])
    COORD_BANCADA_FECHAR = (CONFIG["coordenadas"]["tela_08_fechar_bancada"]["x"],
                            CONFIG["coordenadas"]["tela_08_fechar_bancada"]["y"])
    COORD_DETALHADO = (CONFIG["coordenadas"]["bancada_detalhado"]["x"],
                       CONFIG["coordenadas"]["bancada_detalhado"]["y"])
    COORD_LOCALIZAR = (CONFIG["coordenadas"]["bancada_localizar"]["x"],
                       CONFIG["coordenadas"]["bancada_localizar"]["y"])
    COORD_ORG_CELL = (CONFIG["coordenadas"]["bancada_celula_org"]["x"],
                      CONFIG["coordenadas"]["bancada_celula_org"]["y"])
    TEMPO_ENTRE_CLIQUES = CONFIG["tempos_espera"]["entre_cliques"]
    TEMPO_APOS_MODAL = CONFIG["tempos_espera"]["apos_modal"]
    TEMPO_APOS_ABRIR = CONFIG["tempos_espera"]["apos_abrir_bancada"]
else:
    # Fallback para coordenadas fixas
    COORD_BANCADA_ABRIR = (598, 284)
    COORD_BANCADA_FECHAR = (746, 90)
    COORD_DETALHADO = (273, 358)
    COORD_LOCALIZAR = (524, 689)
    COORD_ORG_CELL = (318, 174)
    TEMPO_ENTRE_CLIQUES = 1.5
    TEMPO_APOS_MODAL = 5.0
    TEMPO_APOS_ABRIR = 3.0
'''

# Substituir coordenadas fixas antigas
old_coord = '''# ===== COORDENADAS FIXAS (1440x900, 100% escala) =====
COORD_DETALHADO = (273, 358)    # Botão "Detalhado"
COORD_LOCALIZAR = (524, 689)    # Botão "Localizar"
COORD_ORG_CELL  = (318, 174)    # Primeira célula da coluna Org.'''

content = content.replace(old_coord, config_code)

# 3. Adicionar funções abrir_bancada e fechar_bancada após focus_oracle
bancada_functions = '''

def abrir_bancada() -> bool:
    """Abre a Bancada de Material com duplo clique"""
    if not _rpa_running:
        return False

    focus_oracle()
    gui_log("📂 Abrindo Bancada de Material (duplo clique)...")

    try:
        x, y = COORD_BANCADA_ABRIR
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        pag.doubleClick()
        gui_log(f"   ✓ Duplo clique em ({x}, {y})")
        time.sleep(TEMPO_APOS_ABRIR)

        focus_oracle()
        gui_log("   ✅ Bancada aberta!")
        return True
    except Exception as e:
        gui_log(f"   ❌ Erro ao abrir bancada: {e}")
        return False

def fechar_bancada() -> bool:
    """Fecha a Bancada de Material clicando no X"""
    if not _rpa_running:
        return False

    focus_oracle()
    gui_log("🔴 Fechando Bancada de Material...")

    try:
        x, y = COORD_BANCADA_FECHAR
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        pag.click()
        gui_log(f"   ✓ Clique em ({x}, {y})")
        time.sleep(TEMPO_ENTRE_CLIQUES)

        gui_log("   ✅ Bancada fechada!")
        return True
    except Exception as e:
        gui_log(f"   ❌ Erro ao fechar bancada: {e}")
        return False
'''

# Inserir após a função focus_oracle
content = content.replace(
    '''def move_click(x, y, right=False):''',
    bancada_functions + '''\ndef move_click(x, y, right=False):'''
)

# 4. Adicionar autenticação Google Sheets no início do run_once
auth_code = '''    # AUTENTICAR GOOGLE SHEETS (primeira vez)
    global _google_authenticated
    if not hasattr(run_once, '_google_authenticated'):
        run_once._google_authenticated = False

    if not run_once._google_authenticated and GOOGLE_SHEETS_AVAILABLE:
        gui_log("=" * 70)
        gui_log("🔐 AUTENTICANDO GOOGLE SHEETS (PRIMEIRA VEZ)")
        gui_log("=" * 70)

        try:
            from google_sheets_manager import get_sheets_service
            gui_log("   Verificando autenticação...")

            # Isso vai abrir o navegador se não tiver token
            service = get_sheets_service()

            gui_log("   ✅ GOOGLE SHEETS AUTENTICADO!")
            run_once._google_authenticated = True
        except Exception as e:
            gui_log(f"   ⚠️ Erro na autenticação: {e}")
            gui_log("   Continuando sem Google Sheets...")

        gui_log("=" * 70)
        gui_log("")

    # ABRIR BANCADA
    if not abrir_bancada():
        gui_log("❌ Falha ao abrir bancada")
        return False

    '''

# Inserir no início do run_once (após verificação de _rpa_running)
content = content.replace(
    '''def run_once() -> bool:
    """
    Executa um ciclo completo do RPA.
    Retorna True se bem-sucedido, False caso contrário.
    """
    if not _rpa_running:
        return False

    focus_oracle()

    # 1) Clicar em "Detalhado" usando coordenadas fixas''',
    '''def run_once() -> bool:
    """
    Executa um ciclo completo do RPA.
    Retorna True se bem-sucedido, False caso contrário.
    """
    if not _rpa_running:
        return False

''' + auth_code + '''    # 1) Clicar em "Detalhado" usando coordenadas fixas'''
)

# 5. Adicionar fechar_bancada no final do run_once (antes do return True)
content = content.replace(
    '''                gui_log("✅ Dados enviados com sucesso para Google Sheets (com Codigo e Data)!")
                return True''',
    '''                gui_log("✅ Dados enviados com sucesso para Google Sheets (com Codigo e Data)!")

                # FECHAR BANCADA
                fechar_bancada()

                return True'''
)

content = content.replace(
    '''        gui_log("⚠️ Google Sheets NÃO CONFIGURADO (GOOGLE_SHEETS_AVAILABLE=False)")
        gui_log("💡 Verifique se google_sheets_manager.py foi incluído no executável")
        return arquivo_salvo is not None''',
    '''        gui_log("⚠️ Google Sheets NÃO CONFIGURADO (GOOGLE_SHEETS_AVAILABLE=False)")
        gui_log("💡 Verifique se google_sheets_manager.py foi incluído no executável")

        # FECHAR BANCADA
        fechar_bancada()

        return arquivo_salvo is not None'''
)

# 6. Modificar main() para loop infinito
content = content.replace(
    '''def main(single_run=True):
    """Função principal do RPA - pode ser chamada pela GUI ou linha de comando"""
    global _rpa_running
    _rpa_running = True

    gui_log("🤖 Robô iniciado. FAILSAFE: canto sup/esq. Ctrl+C para parar.")

    if single_run:
        gui_log("🎯 Modo execução única ativado - finalizar após sucesso")
    else:
        gui_log("🔄 Modo loop contínuo ativado")''',
    '''def main(single_run=False):
    """Função principal do RPA - pode ser chamada pela GUI ou linha de comando"""
    global _rpa_running
    _rpa_running = True

    gui_log("🤖 Robô iniciado. FAILSAFE: canto sup/esq. Ctrl+C para parar.")

    if single_run:
        gui_log("🎯 Modo execução única ativado - finalizar após sucesso")
    else:
        gui_log("🔄 MODO LOOP INFINITO ATIVADO")
        gui_log("   → Abrir bancada → Extrair dados → Fechar bancada → Repetir")
        gui_log("")''')

# Salvar o arquivo modificado
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] main.py atualizado com modo loop infinito!")
print("")
print("Modificacoes aplicadas:")
print("  1. [OK] Importacao de json")
print("  2. [OK] Carregamento de config.json")
print("  3. [OK] Funcao abrir_bancada()")
print("  4. [OK] Funcao fechar_bancada()")
print("  5. [OK] Autenticacao Google Sheets no inicio")
print("  6. [OK] Modo loop infinito (single_run=False)")
print("")
print("[AVISO] Lembre-se de:")
print("  - Verificar se config.json esta na mesma pasta")
print("  - Ajustar coordenadas no config.json se necessario")
print("  - Fazer novo build: pyinstaller RPA_Bancada.spec")
