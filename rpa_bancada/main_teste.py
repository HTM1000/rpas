# -*- coding: utf-8 -*-
"""
RPA BANCADA - MODO TESTE
Executa 3 ciclos rápidos para testar coordenadas do mouse
NÃO conecta ao Google Sheets, NÃO processa dados reais
"""
import time
from pathlib import Path
import sys
import os
import json

import pyautogui as pag

# =================== CONFIG ===================
BASE = Path(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__))))

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
else:
    # Fallback para coordenadas fixas
    COORD_BANCADA_ABRIR = (598, 284)
    COORD_BANCADA_FECHAR = (746, 90)
    COORD_DETALHADO = (273, 358)
    COORD_LOCALIZAR = (524, 689)
    COORD_ORG_CELL = (318, 174)

# ===== CONFIGURAÇÕES DE TIMING (MODO TESTE - RÁPIDO) =====
pag.FAILSAFE = True              # Mover mouse para canto superior esquerdo para parar
pag.PAUSE = 0.1                  # Pausa entre comandos PyAutoGUI (reduzido)
MOUSE_MOVE_DUR = 0.3             # Duração do movimento do mouse (reduzido)
SLEEP_POS_CLIQUE = 0.3           # Pausa após clique (reduzido)
SLEEP_ABERTURA = 0.5             # Pausa após abrir janela (reduzido)

# ===== TEMPOS DE ESPERA MODO TESTE (MUITO CURTOS) =====
TEMPO_APOS_ABRIR = 1.0           # 1 segundo ao invés de 3
TEMPO_APOS_LOCALIZAR = 3.0       # 3 segundos ao invés de 120 (2 min)
TEMPO_PROCESSAMENTO = 3.0        # 3 segundos ao invés de 900 (15 min)

# =================== HELPERS ===================
_rpa_running = True

def move_click(x, y, right=False):
    """Move o mouse e clica na coordenada especificada"""
    print(f"   🖱️ Movendo para ({x}, {y})...")
    pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
    print(f"   👆 Clicando {'direito' if right else 'esquerdo'} em ({x}, {y})")
    pag.click(button='right' if right else 'left')
    time.sleep(SLEEP_POS_CLIQUE)

def abrir_bancada() -> bool:
    """Abre a Bancada de Material com duplo clique"""
    if not _rpa_running:
        return False

    print("\n📂 ABRINDO BANCADA DE MATERIAL (duplo clique)...")

    try:
        x, y = COORD_BANCADA_ABRIR
        print(f"   🖱️ Movendo para ({x}, {y})...")
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        print(f"   👆👆 DUPLO CLIQUE em ({x}, {y})")
        pag.doubleClick()
        time.sleep(TEMPO_APOS_ABRIR)

        print("   ✅ Bancada aberta (simulado)!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao abrir bancada: {e}")
        return False

def fechar_bancada() -> bool:
    """Fecha a Bancada de Material clicando no X"""
    if not _rpa_running:
        return False

    print("\n🔴 FECHANDO BANCADA DE MATERIAL...")

    try:
        x, y = COORD_BANCADA_FECHAR
        print(f"   🖱️ Movendo para ({x}, {y})...")
        pag.moveTo(x, y, duration=MOUSE_MOVE_DUR)
        print(f"   👆 Clicando no X em ({x}, {y})")
        pag.click()
        time.sleep(0.5)

        print("   ✅ Bancada fechada (simulado)!")
        return True
    except Exception as e:
        print(f"   ❌ Erro ao fechar bancada: {e}")
        return False

# =================== UM CICLO ===================
def run_once() -> bool:
    """
    Executa um ciclo completo do RPA TESTE.
    SEMPRE fecha a bancada no final (try/finally).
    """
    if not _rpa_running:
        return False

    # ABRIR BANCADA
    if not abrir_bancada():
        print("❌ Falha ao abrir bancada")
        return False

    sucesso_ciclo = False

    try:
        # 1) Clicar em "Detalhado"
        print("\n🖱️ ETAPA 1: Clicando em 'Detalhado'...")
        move_click(*COORD_DETALHADO)

        if not _rpa_running:
            return False

        # 2) Clicar em "Localizar"
        print("\n🖱️ ETAPA 2: Clicando em 'Localizar'...")
        move_click(*COORD_LOCALIZAR)

        # Dar tempo para a grade carregar (MODO TESTE: só 3 segundos)
        print(f"\n⏳ ETAPA 3: Aguardando {TEMPO_APOS_LOCALIZAR} segundos (grid carregar - MODO TESTE)...")
        time.sleep(TEMPO_APOS_LOCALIZAR)

        if not _rpa_running:
            return False

        # 3) Clicar na primeira célula da coluna 'Org.'
        print("\n🖱️ ETAPA 4: Clicando na célula 'Org'...")
        move_click(*COORD_ORG_CELL)

        if not _rpa_running:
            return False

        # 4) Simular menu contexto
        print("\n⌨️ ETAPA 5: Simulando menu contexto (Shift+F10)...")
        print("   (MODO TESTE: não pressiona teclas reais)")
        time.sleep(0.5)

        # 5) Simular navegação menu
        print("\n⌨️ ETAPA 6: Simulando navegação menu (3x Down + Enter)...")
        print("   (MODO TESTE: não pressiona teclas reais)")
        time.sleep(0.5)

        if not _rpa_running:
            return False

        # 6) Simular processamento Oracle
        print(f"\n⏳ ETAPA 7: Simulando processamento Oracle ({TEMPO_PROCESSAMENTO} segundos - MODO TESTE)...")
        time.sleep(TEMPO_PROCESSAMENTO)

        if not _rpa_running:
            return False

        # 7) Simular leitura clipboard
        print("\n📋 ETAPA 8: Simulando leitura de clipboard...")
        print("   (MODO TESTE: não lê dados reais)")
        time.sleep(0.3)

        # 8) Simular processamento dados
        print("\n📊 ETAPA 9: Simulando processamento de dados...")
        print("   (MODO TESTE: não processa dados reais)")
        time.sleep(0.3)

        # 9) Simular salvamento
        print("\n💾 ETAPA 10: Simulando salvamento Excel...")
        print("   (MODO TESTE: não salva arquivo real)")
        time.sleep(0.3)

        print("\n☁️ ETAPA 11: Google Sheets DESABILITADO (MODO TESTE)")

        sucesso_ciclo = True

    finally:
        # SEMPRE FECHAR BANCADA no final do ciclo
        if _rpa_running:
            print("\n" + "="*70)
            print("🔄 FINALIZANDO CICLO - Fechando bancada...")
            print("="*70)
            fechar_bancada()

    return sucesso_ciclo

# =================== LOOP ===================
def main():
    """Função principal do RPA TESTE - executa EXATAMENTE 3 ciclos"""
    global _rpa_running
    _rpa_running = True

    print("\n" + "="*70)
    print("🧪 RPA BANCADA - MODO TESTE")
    print("="*70)
    print("⚙️ Configurações:")
    print(f"   • Cliques rápidos (sem esperas longas)")
    print(f"   • NÃO conecta Google Sheets")
    print(f"   • NÃO processa dados reais")
    print(f"   • Executa EXATAMENTE 3 ciclos")
    print(f"   • FAILSAFE: canto superior esquerdo para parar")
    print("="*70)
    print()

    # Aguardar 3 segundos para usuário posicionar janelas
    print("⏳ Aguardando 3 segundos para você posicionar as janelas...")
    for i in range(3, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
    print("   🚀 INICIANDO!\n")

    NUM_CICLOS = 3  # EXATAMENTE 3 CICLOS

    try:
        for ciclo in range(1, NUM_CICLOS + 1):
            if not _rpa_running:
                break

            print("\n" + "╔" + "="*68 + "╗")
            print(f"║  🔄 CICLO #{ciclo} de {NUM_CICLOS}                                                    ║")
            print("╚" + "="*68 + "╝\n")

            ok = run_once()

            if ok:
                print("\n" + "="*70)
                print(f"✅ CICLO #{ciclo} CONCLUÍDO COM SUCESSO!")
                print("="*70)
            else:
                if _rpa_running:
                    print("\n" + "="*70)
                    print(f"❌ CICLO #{ciclo} FALHOU!")
                    print("="*70)

            # Aguardar 2 segundos entre ciclos (exceto no último)
            if ciclo < NUM_CICLOS and _rpa_running:
                print("\n⏸️ Aguardando 2 segundos antes do próximo ciclo...\n")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n🛑 INTERROMPIDO PELO USUÁRIO (Ctrl+C).")
    except pag.FailSafeException:
        print("\n🛑 FAILSAFE ACIONADO (mouse no canto superior esquerdo).")
    except Exception as e:
        print(f"\n❌ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
    finally:
        _rpa_running = False
        print("\n" + "="*70)
        print("🏁 TESTE FINALIZADO")
        print("="*70)
        print(f"📊 Resumo:")
        print(f"   • Coordenadas testadas:")
        print(f"     - Abrir Bancada: {COORD_BANCADA_ABRIR}")
        print(f"     - Botão Detalhado: {COORD_DETALHADO}")
        print(f"     - Botão Localizar: {COORD_LOCALIZAR}")
        print(f"     - Célula Org: {COORD_ORG_CELL}")
        print(f"     - Fechar Bancada: {COORD_BANCADA_FECHAR}")
        print(f"   • Ciclos executados: {min(ciclo, NUM_CICLOS)}/{NUM_CICLOS}")
        print("="*70)

if __name__ == "__main__":
    main()
