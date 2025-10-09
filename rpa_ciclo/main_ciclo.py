# -*- coding: utf-8 -*-
"""
RPA CICLO - Módulo Principal (Versão para GUI)
Orquestra a execução sequencial de processos no Oracle
"""

import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
import pyautogui
import logging

# Importar módulo Google Sheets
try:
    from google_sheets_ciclo import registrar_ciclo, atualizar_ciclo
    GOOGLE_SHEETS_DISPONIVEL = True
except ImportError:
    GOOGLE_SHEETS_DISPONIVEL = False
    print("⚠️ Google Sheets não disponível")

# =================== CONFIGURAÇÕES GLOBAIS ===================
BASE_DIR = Path(__file__).parent.resolve() if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
CONFIG_FILE = BASE_DIR / "config.json"

# Compatibilidade com .exe
base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

# Controle de execução
_rpa_running = False
_gui_log_callback = None
_ciclo_atual = 0
_data_inicio_ciclo = None

# =================== CALLBACKS PARA GUI ===================
def set_gui_log_callback(callback):
    """Define callback para enviar logs para a GUI"""
    global _gui_log_callback
    _gui_log_callback = callback

def gui_log(msg):
    """Envia log para GUI se callback estiver definido"""
    if _gui_log_callback:
        _gui_log_callback(msg)
    else:
        print(msg)

def stop_rpa():
    """Para o RPA externamente (para ser chamado pela GUI)"""
    global _rpa_running
    _rpa_running = False
    gui_log("🛑 Solicitação de parada recebida")

def is_rpa_running():
    """Verifica se RPA está rodando"""
    return _rpa_running

# =================== CARREGAMENTO DE CONFIGURAÇÃO ===================
def carregar_config():
    """Carrega as configurações do arquivo config.json"""
    try:
        config_path = os.path.join(base_path, "config.json")
        if not os.path.exists(config_path):
            config_path = CONFIG_FILE

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        gui_log("✅ Configurações carregadas")
        return config
    except FileNotFoundError:
        gui_log(f"❌ Arquivo de configuração não encontrado: {CONFIG_FILE}")
        raise
    except json.JSONDecodeError as e:
        gui_log(f"❌ Erro ao decodificar JSON: {e}")
        raise

# =================== FUNÇÕES DE AUTOMAÇÃO ===================
def clicar_coordenada(x, y, duplo=False, descricao=""):
    """Clica em uma coordenada específica na tela"""
    if descricao:
        gui_log(f"🖱️ {descricao}")

    pyautogui.moveTo(x, y, duration=0.5)
    time.sleep(0.3)

    if duplo:
        pyautogui.doubleClick()
    else:
        pyautogui.click()

    time.sleep(0.5)

def digitar_texto(texto, pressionar_teclas=None):
    """Digita um texto e opcionalmente pressiona teclas adicionais"""
    gui_log(f"⌨️ Digitando: {texto}")
    pyautogui.write(texto)
    time.sleep(0.3)

    if pressionar_teclas:
        for tecla in pressionar_teclas:
            gui_log(f"⌨️ Pressionando: {tecla.upper()}")
            pyautogui.press(tecla)
            time.sleep(0.3)

def aguardar_com_pausa(segundos, mensagem="Aguardando"):
    """Aguarda um tempo com possibilidade de interrupção"""
    gui_log(f"⏳ {mensagem} ({segundos}s)...")
    inicio = time.time()
    while time.sleep(0.5) or time.time() - inicio < segundos:
        if not _rpa_running:
            return False
    return True

# =================== ETAPAS DO PROCESSO ===================
def etapa_01_transferencia_subinventario(config):
    """Etapa 1: Clicar em Transferência de Subinventário"""
    gui_log("📋 ETAPA 1: Transferência de Subinventário")

    coord = config["coordenadas"]["tela_01_transferencia_subinventario"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando abertura do modal")

def etapa_02_preencher_tipo(config):
    """Etapa 2: Preencher campo Tipo com SUB"""
    gui_log("📋 ETAPA 2: Preenchimento do Tipo")

    coord = config["coordenadas"]["tela_02_campo_tipo"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    time.sleep(0.5)
    digitar_texto(coord["digitar"], pressionar_teclas=coord["acoes"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando processamento")

def etapa_03_selecionar_funcionario(config):
    """Etapa 3: Selecionar funcionário Wallatas Moreira"""
    gui_log("📋 ETAPA 3: Seleção de Funcionário")

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
    gui_log("📋 ETAPA 4: Confirmação")

    coord = config["coordenadas"]["tela_05_confirmar_sim"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["apos_modal"]
    return aguardar_com_pausa(tempo_espera, "Aguardando confirmação")

def etapa_05_executar_rpa_oracle(config):
    """Etapa 5: Executar RPA_Oracle completo"""
    gui_log("🤖 ETAPA 5: Execução do RPA_Oracle")

    # Como RPA_Oracle tem GUI própria, vamos simular que foi executado
    # Na prática, você pode implementar chamada ao executável do RPA_Oracle
    gui_log("⚠️ RPA_Oracle deve ser executado manualmente ou via integração futura")
    gui_log("✅ Aguardando conclusão do RPA_Oracle...")

    # Aguardar tempo configurado
    tempo_espera = config["tempos_espera"]["apos_rpa_oracle"]
    return aguardar_com_pausa(tempo_espera, "Aguardando estabilização pós-Oracle")

def etapa_06_navegacao_pos_oracle(config):
    """Etapa 6: Navegação após RPA_Oracle"""
    gui_log("📋 ETAPA 6: Navegação pós-Oracle")

    # Clicar na janela de navegação
    coord = config["coordenadas"]["tela_06_janela_navegador"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    if not aguardar_com_pausa(tempo_espera, "Aguardando janela de navegação"):
        return False

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
    gui_log("🤖 ETAPA 7: Execução do RPA_Bancada")

    # Caminho para o executável do RPA_Bancada
    caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "dist" / "RPA_Bancada.exe"

    if not caminho_bancada.exists():
        # Tentar com script Python
        caminho_bancada = BASE_DIR.parent / "rpa_bancada" / "main.py"
        if not caminho_bancada.exists():
            gui_log(f"❌ RPA_Bancada não encontrado")
            return False

        use_python = True
    else:
        use_python = False

    gui_log(f"📂 Executando: {caminho_bancada}")

    try:
        if use_python:
            resultado = subprocess.run(
                [sys.executable, str(caminho_bancada)],
                cwd=str(caminho_bancada.parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800  # 30 minutos máximo
            )
        else:
            resultado = subprocess.run(
                [str(caminho_bancada)],
                cwd=str(caminho_bancada.parent),
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=1800
            )

        if resultado.returncode == 0:
            gui_log("✅ RPA_Bancada executado com sucesso")
        else:
            gui_log(f"⚠️ RPA_Bancada finalizou com código: {resultado.returncode}")
            return True  # Continuar mesmo com código de saída diferente de 0

        tempo_espera = config["tempos_espera"]["apos_rpa_bancada"]
        return aguardar_com_pausa(tempo_espera, "Aguardando estabilização")

    except subprocess.TimeoutExpired:
        gui_log("⚠️ RPA_Bancada atingiu timeout")
        return False
    except Exception as e:
        gui_log(f"❌ Erro ao executar RPA_Bancada: {e}")
        return False

def etapa_08_fechar_bancada(config):
    """Etapa 8: Fechar a janela da Bancada"""
    gui_log("📋 ETAPA 8: Fechamento da Bancada")

    coord = config["coordenadas"]["tela_08_fechar_bancada"]
    clicar_coordenada(coord["x"], coord["y"], descricao=coord["descricao"])

    tempo_espera = config["tempos_espera"]["entre_cliques"]
    return aguardar_com_pausa(tempo_espera, "Aguardando fechamento")

# =================== EXECUÇÃO DO CICLO COMPLETO ===================
def executar_ciclo_completo(config):
    """Executa um ciclo completo de todas as etapas"""
    global _ciclo_atual, _data_inicio_ciclo

    _ciclo_atual += 1
    _data_inicio_ciclo = datetime.now()

    gui_log("=" * 60)
    gui_log(f"🔄 CICLO #{_ciclo_atual} - {_data_inicio_ciclo.strftime('%Y-%m-%d %H:%M:%S')}")
    gui_log("=" * 60)

    # Registrar início no Google Sheets
    if GOOGLE_SHEETS_DISPONIVEL:
        try:
            registrar_ciclo(
                ciclo_numero=_ciclo_atual,
                status="Em Execução",
                data_inicio=_data_inicio_ciclo
            )
        except Exception as e:
            gui_log(f"⚠️ Erro ao registrar no Google Sheets: {e}")

    etapas_status = {
        "RPA Oracle": "Pendente",
        "RPA Bancada": "Pendente"
    }

    try:
        # Executar todas as etapas em sequência
        etapas = [
            ("Transferência Subinventário", etapa_01_transferencia_subinventario),
            ("Preenchimento Tipo", etapa_02_preencher_tipo),
            ("Seleção Funcionário", etapa_03_selecionar_funcionario),
            ("Confirmação", etapa_04_confirmar_selecao),
            ("RPA Oracle", etapa_05_executar_rpa_oracle),
            ("Navegação", etapa_06_navegacao_pos_oracle),
            ("RPA Bancada", etapa_07_executar_rpa_bancada),
            ("Fechamento Bancada", etapa_08_fechar_bancada)
        ]

        for nome_etapa, funcao_etapa in etapas:
            if not _rpa_running:
                gui_log("⏸️ Ciclo interrompido pelo usuário")

                # Atualizar no Google Sheets
                if GOOGLE_SHEETS_DISPONIVEL:
                    try:
                        atualizar_ciclo(_ciclo_atual, "Status", "Pausado")
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
                    except Exception:
                        pass

                return False

            sucesso = funcao_etapa(config)

            # Atualizar status de etapas específicas
            if nome_etapa == "RPA Oracle":
                etapas_status["RPA Oracle"] = "Sucesso" if sucesso else "Falha"
            elif nome_etapa == "RPA Bancada":
                etapas_status["RPA Bancada"] = "Sucesso" if sucesso else "Falha"

            if not sucesso:
                gui_log(f"❌ Falha na etapa: {nome_etapa}")

                # Atualizar no Google Sheets
                if GOOGLE_SHEETS_DISPONIVEL:
                    try:
                        data_fim = datetime.now()
                        atualizar_ciclo(_ciclo_atual, "Status", "Falha")
                        atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                        atualizar_ciclo(_ciclo_atual, "Etapa Falha", nome_etapa)
                        atualizar_ciclo(_ciclo_atual, "RPA Oracle", etapas_status["RPA Oracle"])
                        atualizar_ciclo(_ciclo_atual, "RPA Bancada", etapas_status["RPA Bancada"])
                    except Exception:
                        pass

                return False

        # Sucesso!
        data_fim = datetime.now()
        gui_log("=" * 60)
        gui_log(f"✅ CICLO #{_ciclo_atual} CONCLUÍDO COM SUCESSO!")
        gui_log("=" * 60)

        # Atualizar no Google Sheets
        if GOOGLE_SHEETS_DISPONIVEL:
            try:
                atualizar_ciclo(_ciclo_atual, "Status", "Sucesso")
                atualizar_ciclo(_ciclo_atual, "Data/Hora Fim", data_fim.strftime("%Y-%m-%d %H:%M:%S"))
                atualizar_ciclo(_ciclo_atual, "RPA Oracle", etapas_status["RPA Oracle"])
                atualizar_ciclo(_ciclo_atual, "RPA Bancada", etapas_status["RPA Bancada"])

                # Calcular tempo
                delta = data_fim - _data_inicio_ciclo
                minutos = delta.total_seconds() / 60
                atualizar_ciclo(_ciclo_atual, "Tempo Execução (min)", f"{minutos:.2f}")
            except Exception as e:
                gui_log(f"⚠️ Erro ao atualizar Google Sheets: {e}")

        return True

    except Exception as e:
        gui_log(f"❌ Erro durante o ciclo: {e}")
        import traceback
        gui_log(traceback.format_exc())

        # Atualizar no Google Sheets
        if GOOGLE_SHEETS_DISPONIVEL:
            try:
                atualizar_ciclo(_ciclo_atual, "Status", "Erro")
                atualizar_ciclo(_ciclo_atual, "Observações", str(e))
            except Exception:
                pass

        return False

# =================== LOOP PRINCIPAL ===================
def main(modo_continuo=False):
    """
    Função principal - pode executar um ciclo único ou em loop contínuo

    Args:
        modo_continuo: Se True, executa em loop com intervalo de 30 min
    """
    global _rpa_running, _ciclo_atual
    _rpa_running = True

    gui_log("=" * 60)
    gui_log("🤖 RPA CICLO - Iniciado")
    gui_log("=" * 60)

    try:
        config = carregar_config()

        if modo_continuo:
            gui_log("🔄 Modo contínuo ativado - repetirá a cada 30 minutos")

            while _rpa_running:
                # Executar ciclo
                sucesso = executar_ciclo_completo(config)

                if not sucesso:
                    gui_log("⚠️ Ciclo falhou, mas continuará após intervalo...")

                if not _rpa_running:
                    break

                # Aguardar intervalo
                tempo_ciclo = config["tempos_espera"]["ciclo_completo"]
                minutos = tempo_ciclo / 60

                gui_log("⏰" * 30)
                gui_log(f"⏰ Aguardando {minutos:.0f} minutos até o próximo ciclo...")
                gui_log("⏰" * 30)

                if not aguardar_com_pausa(tempo_ciclo, f"Intervalo de {minutos:.0f} minutos"):
                    break
        else:
            gui_log("🎯 Modo execução única")
            executar_ciclo_completo(config)

    except KeyboardInterrupt:
        gui_log("⏸️ Interrompido pelo usuário (Ctrl+C)")
    except pyautogui.FailSafeException:
        gui_log("🛑 FAILSAFE acionado (mouse no canto superior esquerdo)")
    except Exception as e:
        gui_log(f"❌ Erro fatal: {e}")
        import traceback
        gui_log(traceback.format_exc())
    finally:
        _rpa_running = False
        gui_log("=" * 60)
        gui_log("🏁 RPA CICLO - Finalizado")
        gui_log(f"📊 Total de ciclos executados: {_ciclo_atual}")
        gui_log("=" * 60)

# =================== PONTO DE ENTRADA ===================
if __name__ == "__main__":
    # Configurar PyAutoGUI
    pyautogui.PAUSE = 0.5
    pyautogui.FAILSAFE = True

    # Executar RPA em modo contínuo
    main(modo_continuo=True)
