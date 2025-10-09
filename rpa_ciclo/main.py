# -*- coding: utf-8 -*-
"""
RPA CICLO - Automação de Ciclo Completo
Orquestra a execução sequencial de processos no Oracle, incluindo:
- Transferência de Subinventário
- Execução do RPA_Oracle
- Navegação e execução do RPA_Bancada
- Repetição automática com intervalo de 30 minutos
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
import pyautogui
import keyboard
import logging
from datetime import datetime

# =================== CONFIGURAÇÃO DE LOGS ===================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpa_ciclo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =================== CONFIGURAÇÕES GLOBAIS ===================
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"

# Controle de execução
estado_rpa = {
    "executando": True,
    "ciclo_atual": 0
}

# =================== CARREGAMENTO DE CONFIGURAÇÃO ===================
def carregar_config():
    """Carrega as configurações do arquivo config.json"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        logger.info("✅ Configurações carregadas com sucesso")
        return config
    except FileNotFoundError:
        logger.error(f"❌ Arquivo de configuração não encontrado: {CONFIG_FILE}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar JSON: {e}")
        raise

# =================== FUNÇÕES DE CONTROLE ===================
def verificar_pausa():
    """Verifica se o usuário pressionou ESC para pausar"""
    if keyboard.is_pressed('esc'):
        logger.warning("⏸️ ESC pressionado - Pausando RPA...")
        estado_rpa["executando"] = False
        return True
    return False

def aguardar_com_pausa(segundos, mensagem="Aguardando"):
    """Aguarda um tempo com possibilidade de interrupção por ESC"""
    logger.info(f"⏳ {mensagem} por {segundos} segundos...")
    inicio = time.time()
    while time.time() - inicio < segundos:
        if verificar_pausa():
            return False
        time.sleep(0.5)
    return True

# =================== FUNÇÕES DE AUTOMAÇÃO ===================
def clicar_coordenada(x, y, duplo=False, descricao=""):
    """Clica em uma coordenada específica na tela"""
    if descricao:
        logger.info(f"🖱️ {descricao}")
    else:
        logger.info(f"🖱️ Clicando em ({x}, {y})")

    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.3)

    if duplo:
        pyautogui.doubleClick()
    else:
        pyautogui.click()

    time.sleep(0.5)

def digitar_texto(texto, pressionar_teclas=None):
    """Digita um texto e opcionalmente pressiona teclas adicionais"""
    logger.info(f"⌨️ Digitando: {texto}")
    pyautogui.write(texto)
    time.sleep(0.3)

    if pressionar_teclas:
        for tecla in pressionar_teclas:
            logger.info(f"⌨️ Pressionando: {tecla.upper()}")
            pyautogui.press(tecla)
            time.sleep(0.3)

# =================== ETAPAS DO PROCESSO ===================
def etapa_01_transferencia_subinventario(config):
    """Etapa 1: Clicar em Transferência de Subinventário"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 1: Transferência de Subinventário")
    logger.info("="*60)

    coord = config["coordenadas"]["tela_01_transferencia_subinventario"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura do modal")

def etapa_02_preencher_tipo(config):
    """Etapa 2: Preencher campo Tipo com SUB"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 2: Preenchimento do Tipo")
    logger.info("="*60)

    coord = config["coordenadas"]["tela_02_campo_tipo"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    time.sleep(0.5)
    digitar_texto(coord["digitar"], pressionar_teclas=coord["acoes"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando processamento")

def etapa_03_selecionar_funcionario(config):
    """Etapa 3: Selecionar funcionário Wallatas Moreira"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 3: Seleção de Funcionário")
    logger.info("="*60)

    # Clicar na pastinha
    coord_pastinha = config["coordenadas"]["tela_03_pastinha_funcionario"]
    clicar_coordenada(coord_pastinha["x"], coord_pastinha["y"], descricao=coord_pastinha["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando modal de funcionários"):
        return False

    # Duplo clique em Wallatas Moreira
    coord_wallatas = config["coordenadas"]["tela_04_selecionar_wallatas"]
    clicar_coordenada(
        coord_wallatas["x"],
        coord_wallatas["y"],
        duplo=coord_wallatas.get("duplo_clique", False),
        descricao=coord_wallatas["descricao"]
    )

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando seleção")

def etapa_04_confirmar_selecao(config):
    """Etapa 4: Confirmar seleção clicando em Sim"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 4: Confirmação")
    logger.info("="*60)

    coord = config["coordenadas"]["tela_05_confirmar_sim"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando confirmação")

def etapa_05_executar_rpa_oracle(config):
    """Etapa 5: Executar RPA_Oracle completo"""
    logger.info("\n" + "="*60)
    logger.info("🤖 ETAPA 5: Execução do RPA_Oracle")
    logger.info("="*60)

    caminho_oracle = BASE_DIR.parent / "rpa_oracle" / "RPA_Oracle.py"

    if not caminho_oracle.exists():
        logger.error(f"❌ RPA_Oracle não encontrado em: {caminho_oracle}")
        return False

    logger.info(f"📂 Executando: {caminho_oracle}")

    try:
        # Executar RPA_Oracle como subprocesso
        # Nota: Como o RPA_Oracle tem GUI Tkinter, ele precisa ser executado e controlado manualmente
        # Aqui vamos apenas iniciar o processo e aguardar ele terminar
        logger.warning("⚠️ RPA_Oracle possui interface gráfica própria")
        logger.warning("⚠️ Por favor, execute o RPA_Oracle manualmente e aguarde sua conclusão")
        logger.warning("⚠️ Quando o RPA_Oracle terminar, pressione ENTER para continuar...")

        input()  # Aguarda o usuário pressionar ENTER

        logger.info("✅ Continuando após execução do RPA_Oracle")

        tempo_espera = config["tempos_espera"]["apos_rpa_oracle"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

    except Exception as e:
        logger.error(f"❌ Erro ao executar RPA_Oracle: {e}")
        return False

def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação após RPA_Oracle"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 6: Navegação pós-Oracle")
    logger.info("="*60)

    # Clicar na janela de navegação
    coord = config["coordenadas"]["tela_06_janela_navegador"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando janela de navegação"):
        return False

    logger.info(f"ℹ️ Verificando opção: {config['textos']['navegador_opcao']}")

    # Clicar duplo em "4. Bancada de Material"
    coord_bancada = config["coordenadas"]["tela_07_bancada_material"]
    clicar_coordenada(
        coord_bancada["x"],
        coord_bancada["y"],
        duplo=coord_bancada.get("duplo_clique", False),
        descricao=coord_bancada["descricao"]
    )

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura da Bancada")

def etapa_07_executar_rpa_bancada(config):
    """Etapa 7: Executar RPA_Bancada completo"""
    logger.info("\n" + "="*60)
    logger.info("🤖 ETAPA 7: Execução do RPA_Bancada")
    logger.info("="*60)

    caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "main.py"

    if not caminho_bancada.exists():
        logger.error(f"❌ RPA_Bancada não encontrado em: {caminho_bancada}")
        return False

    logger.info(f"📂 Executando: {caminho_bancada}")

    try:
        # Executar RPA_Bancada como subprocesso
        resultado = subprocess.run(
            [sys.executable, str(caminho_bancada)],
            cwd=str(caminho_bancada.parent),
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if resultado.returncode == 0:
            logger.info("✅ RPA_Bancada executado com sucesso")
            logger.debug(f"Output: {resultado.stdout}")
        else:
            logger.error(f"❌ RPA_Bancada falhou com código: {resultado.returncode}")
            logger.error(f"Erro: {resultado.stderr}")
            return False

        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

    except Exception as e:
        logger.error(f"❌ Erro ao executar RPA_Bancada: {e}")
        return False

def etapa_08_fechar_bancada(config):
    """Etapa 8: Fechar a janela da Bancada"""
    logger.info("\n" + "="*60)
    logger.info("📋 ETAPA 8: Fechamento da Bancada")
    logger.info("="*60)

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando fechamento")

# =================== EXECUÇÃO DO CICLO COMPLETO ===================
def executar_ciclo_completo(config):
    """Executa um ciclo completo de todas as etapas"""
    estado_rpa["ciclo_atual"] += 1

    logger.info("\n" + "🔄"*30)
    logger.info(f"🔄 INICIANDO CICLO #{estado_rpa['ciclo_atual']}")
    logger.info(f"🕐 Horário: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("🔄"*30 + "\n")

    try:
        # Executar todas as etapas em sequência
        etapas = [
            etapa_01_transferencia_subinventario,
            etapa_02_preencher_tipo,
            etapa_03_selecionar_funcionario,
            etapa_04_confirmar_selecao,
            etapa_05_executar_rpa_oracle,
            etapa_06_navegacao_pos_oracle,
            etapa_07_executar_rpa_bancada,
            etapa_08_fechar_bancada
        ]

        for i, etapa in enumerate(etapas, 1):
            if not estado_rpa["executando"]:
                logger.warning("⏸️ Ciclo interrompido pelo usuário")
                return False

            sucesso = etapa(config)

            if not sucesso:
                logger.error(f"❌ Falha na etapa {i}: {etapa.__name__}")
                return False

        logger.info("\n" + "✅"*30)
        logger.info(f"✅ CICLO #{estado_rpa['ciclo_atual']} CONCLUÍDO COM SUCESSO!")
        logger.info("✅"*30 + "\n")
        return True

    except Exception as e:
        logger.error(f"❌ Erro durante o ciclo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

# =================== LOOP PRINCIPAL ===================
def main():
    """Função principal - loop contínuo do RPA"""
    logger.info("="*60)
    logger.info("🤖 RPA CICLO - Iniciado")
    logger.info("="*60)
    logger.info("ℹ️ Pressione ESC a qualquer momento para pausar")
    logger.info("="*60 + "\n")

    try:
        config = carregar_config()

        while estado_rpa["executando"]:
            # Executar ciclo completo
            sucesso = executar_ciclo_completo(config)

            if not sucesso:
                logger.warning("⚠️ Ciclo falhou, mas continuará após intervalo...")

            if not estado_rpa["executando"]:
                break

            # Aguardar intervalo de 30 minutos antes do próximo ciclo
            tempo_ciclo = config["tempos_espera"]["ciclo_completo"]
            minutos = tempo_ciclo / 60

            logger.info("\n" + "⏰"*30)
            logger.info(f"⏰ Aguardando {minutos:.0f} minutos até o próximo ciclo...")
            logger.info(f"🕐 Próximo ciclo em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("⏰"*30 + "\n")

            if not aguardar_com_pausa(tempo_ciclo, f"Intervalo de {minutos:.0f} minutos"):
                break

    except KeyboardInterrupt:
        logger.warning("\n⏸️ Interrompido pelo usuário (Ctrl+C)")
    except Exception as e:
        logger.error(f"\n❌ Erro fatal: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        logger.info("\n" + "="*60)
        logger.info("🏁 RPA CICLO - Finalizado")
        logger.info(f"📊 Total de ciclos executados: {estado_rpa['ciclo_atual']}")
        logger.info("="*60)

# =================== PONTO DE ENTRADA ===================
if __name__ == "__main__":
    # Configurar PyAutoGUI
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = True

    # Executar RPA
    main()
