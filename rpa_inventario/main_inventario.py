# -*- coding: utf-8 -*-
"""
RPA INVENTÁRIO - Módulo Principal
Automação Desktop usando PyAutoGUI com detecção de imagem
"""

import os
import sys
import time
import json
import random
from pathlib import Path
import pyautogui
import pyperclip
import keyboard
import ctypes

# Configurar PyAutoGUI
pyautogui.PAUSE = 0.5  # Pausa entre ações
pyautogui.FAILSAFE = True  # Move mouse para canto = parada de emergência

# ─── CONFIGURAÇÃO ──────────────────────────────────────────────────────────
# Diretório base compatível com .exe
if getattr(sys, 'frozen', False):
    # Rodando como executável - arquivos estão em _MEIPASS
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Rodando como script Python
    BASE_DIR = Path(__file__).parent.resolve()

ELEMENTOS_DIR = BASE_DIR / "elementos"

# Carregar configurações
CONFIG_PATH = BASE_DIR / "config.json"

def carregar_config():
    """Carrega configurações do arquivo config.json"""
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"⚠️ config.json não encontrado em {CONFIG_PATH}")
            return {}
    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return {}

CONFIG = carregar_config()

# ─── CONTROLE GLOBAL ────────────────────────────────────────────────────────
_rpa_running = True
_gui_log_callback = None
_modo_teste = False  # Flag global para modo teste
_robo_id = "PC-01"  # ID do robô (padrão)
_item_atual_id = None  # ID do item sendo processado (para tratamento de parada)

def set_gui_log_callback(callback):
    """Define callback para log na interface gráfica"""
    global _gui_log_callback
    _gui_log_callback = callback

def log(msg: str):
    """Envia log para GUI se callback estiver configurado, senão imprime"""
    if _gui_log_callback:
        _gui_log_callback(msg)
    else:
        print(msg)

def stop_rpa():
    """Sinaliza para parar o RPA"""
    global _rpa_running
    _rpa_running = False
    log("🛑 Parada solicitada...")

def check_stop():
    """Verifica se deve parar e lança exceção se sim"""
    if not _rpa_running:
        raise KeyboardInterrupt("RPA interrompido pelo usuário")

# ─── FUNÇÕES DE DETECÇÃO DE IMAGEM ─────────────────────────────────────────
def localizar_imagem(nome_imagem: str, confianca: float = 0.8, timeout: int = 10):
    """
    Localiza uma imagem na tela

    Args:
        nome_imagem: Nome do arquivo de imagem (ex: 'botao_salvar.png')
        confianca: Nível de confiança (0.0 a 1.0)
        timeout: Tempo máximo de espera em segundos

    Returns:
        Posição (x, y) do centro da imagem ou None
    """
    # Se modo teste estiver ativo, buscar em elementos/teste/
    if _modo_teste:
        caminho_imagem = ELEMENTOS_DIR / "teste" / nome_imagem
    else:
        caminho_imagem = ELEMENTOS_DIR / nome_imagem

    if not caminho_imagem.exists():
        log(f"⚠️ Imagem não encontrada: {caminho_imagem}")
        return None

    pasta_msg = " [TESTE]" if _modo_teste else ""
    log(f"🔍 Procurando imagem{pasta_msg}: {nome_imagem} (confiança: {confianca*100}%)")

    tempo_inicio = time.time()
    while time.time() - tempo_inicio < timeout:
        check_stop()

        try:
            posicao = pyautogui.locateOnScreen(
                str(caminho_imagem),
                confidence=confianca
            )

            if posicao:
                centro = pyautogui.center(posicao)
                log(f"✅ Imagem encontrada em: {centro}")
                return centro

        except Exception as e:
            pass

        time.sleep(0.5)

    log(f"⚠️ Imagem '{nome_imagem}' não encontrada após {timeout}s")
    return None

def clicar_imagem(nome_imagem: str, descricao: str = "", confianca: float = 0.8, timeout: int = 10):
    """
    Localiza e clica em uma imagem na tela

    Args:
        nome_imagem: Nome do arquivo de imagem
        descricao: Descrição para log
        confianca: Nível de confiança
        timeout: Tempo máximo de espera
    """
    desc = descricao or nome_imagem
    log(f"🖱️ Clicando em '{desc}'...")

    posicao = localizar_imagem(nome_imagem, confianca, timeout)

    if posicao:
        pyautogui.click(posicao)
        log(f"✅ Clicado em '{desc}'")
        return True
    else:
        log(f"❌ Não foi possível clicar em '{desc}'")
        return False

def esperar(segundos: float, msg: str = ""):
    """Espera X segundos, verificando parada a cada 0.5s"""
    msg_exibida = f" ({msg})" if msg else ""
    log(f"⏳ Aguardando {segundos}s{msg_exibida}...")

    elapsed = 0.0
    intervalo = 0.5

    while elapsed < segundos:
        check_stop()
        time.sleep(min(intervalo, segundos - elapsed))
        elapsed += intervalo

def digitar(texto: str, descricao: str = ""):
    """
    Digita um texto

    Args:
        texto: Texto a digitar
        descricao: Descrição para log
    """
    desc = descricao or "texto"
    log(f"⌨️ Digitando {desc}: {texto}")

    pyautogui.write(str(texto), interval=0.05)

def pressionar_tab(vezes: int = 1):
    """
    Pressiona TAB X vezes

    Args:
        vezes: Número de vezes para pressionar TAB
    """
    log(f"⌨️ Pressionando TAB {vezes}x...")

    for i in range(vezes):
        check_stop()
        pyautogui.press('tab')
        time.sleep(0.2)

def pressionar_enter():
    """Pressiona ENTER"""
    log("⌨️ Pressionando ENTER...")
    pyautogui.press('enter')

def copiar_campo():
    """
    Copia o conteúdo do campo atual usando Ctrl+C

    Returns:
        str: Conteúdo copiado do campo
    """
    log("📋 Copiando conteúdo do campo (Ctrl+C)...")

    # Limpar clipboard antes
    pyperclip.copy('')
    time.sleep(0.2)

    # Selecionar tudo (Ctrl+A) e copiar (Ctrl+C)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.3)  # Aguardar clipboard atualizar

    # Obter conteúdo
    conteudo = pyperclip.paste().strip()
    log(f"✅ Copiado: '{conteudo}'")

    return conteudo

def prevenir_hibernacao():
    """Impede o computador de hibernar (Windows)"""
    try:
        # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        # Mantém o sistema ativo e a tela ligada
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
    except Exception as e:
        log(f"⚠️ Erro ao prevenir hibernação: {e}")

def restaurar_hibernacao():
    """Restaura configurações normais de energia"""
    try:
        # ES_CONTINUOUS (desativa as flags anteriores)
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    except Exception as e:
        log(f"⚠️ Erro ao restaurar hibernação: {e}")

def delay_randomico(min_seg=0.5, max_seg=2.0):
    """
    Adiciona delay randômico para evitar rate-limit

    Args:
        min_seg: Tempo mínimo em segundos
        max_seg: Tempo máximo em segundos
    """
    delay = random.uniform(min_seg, max_seg)
    time.sleep(delay)

# ─── FUNÇÃO PRINCIPAL ───────────────────────────────────────────────────────
def main(inventario: str = "", robo_id: str = "PC-01", tipo_contagem: str = "primeira", tipo_planilha: str = "bc1", modo_teste: bool = False):
    """
    Função principal do RPA Inventário

    Args:
        inventario: Nome do inventário a processar
        robo_id: Identificador único do robô (ex: "PC-01", "PC-02", etc.)
        tipo_contagem: "primeira" ou "segunda" contagem
        tipo_planilha: "bc1" ou "bc2"
        modo_teste: Se True, usa imagens da pasta elementos/teste/
    """
    global _rpa_running, _modo_teste, _robo_id
    _rpa_running = True
    _modo_teste = modo_teste
    _robo_id = robo_id

    # Configurar listener ESC para parada de emergência
    def on_esc():
        log("⚠️ ESC pressionado - parando RPA...")
        stop_rpa()

    keyboard.on_press_key("esc", lambda _: on_esc())

    try:
        # ===============================================================
        # PREVENIR HIBERNAÇÃO DO PC DURANTE EXECUÇÃO
        # ===============================================================
        prevenir_hibernacao()
        log("🔋 Hibernação do PC desabilitada durante execução")

        log("=" * 70)
        log("🤖 RPA INVENTÁRIO - INICIANDO")
        log("=" * 70)
        log("")
        log(f"📋 Inventário: {inventario}")
        log(f"📊 Tipo: {tipo_contagem.title()} Contagem")
        log(f"📁 Planilha: {tipo_planilha.upper()}")
        log(f"🧪 Modo Teste: {'ATIVADO (imagens em elementos/teste/)' if modo_teste else 'Desativado'}")
        log(f"🔄 Modo Contínuo: ATIVADO (verifica a cada 30s)")
        log("📌 Pressione ESC a qualquer momento para parar")
        log("⚠️ FAILSAFE: Mova mouse para canto superior esquerdo para parar")
        log("")

        # Verificar se pasta elementos existe
        log(f"🔍 Procurando pasta elementos em: {ELEMENTOS_DIR}")
        log(f"📁 BASE_DIR: {BASE_DIR}")
        log(f"📂 Diretório atual: {Path.cwd()}")

        if not ELEMENTOS_DIR.exists():
            log(f"❌ Pasta 'elementos' não encontrada em: {ELEMENTOS_DIR}")
            log("ℹ️ Crie a pasta 'elementos' e adicione as imagens dos botões/campos")
            return
        else:
            log(f"✅ Pasta elementos encontrada!")

            # Se modo teste, verificar pasta elementos/teste
            if modo_teste:
                elementos_teste_dir = ELEMENTOS_DIR / "teste"
                if not elementos_teste_dir.exists():
                    log(f"❌ Pasta 'elementos/teste' não encontrada em: {elementos_teste_dir}")
                    log("ℹ️ Crie a pasta 'elementos/teste' e adicione as imagens alternativas")
                    return
                else:
                    log(f"✅ Pasta elementos/teste encontrada!")
                    # Listar imagens disponíveis na pasta teste
                    imagens = list(elementos_teste_dir.glob('*.png'))
                    log(f"📸 {len(imagens)} imagens encontradas em elementos/teste:")
                    for img in imagens:
                        log(f"   - {img.name}")
            else:
                # Listar imagens disponíveis na pasta normal
                imagens = list(ELEMENTOS_DIR.glob('*.png'))
                log(f"📸 {len(imagens)} imagens encontradas:")
                for img in imagens:
                    log(f"   - {img.name}")

        # Buscar dados do Google Sheets
        log("🔍 Buscando dados do Google Sheets...")
        try:
            import google_sheets_inventario as gsheets
            dados = gsheets.buscar_dados_inventario(inventario, tipo_contagem, tipo_planilha)

            if dados:
                log(f"✅ {len(dados)} itens encontrados para '{inventario}' (pendentes de processamento)")
            else:
                log(f"⚠️ Nenhum item pendente encontrado para '{inventario}'")
                log("ℹ️ Todos os itens já foram processados ou o nome do inventário está incorreto")
        except Exception as e:
            log(f"❌ Erro ao buscar dados do Google Sheets: {e}")
            dados = []

        # Aguardar usuário posicionar na tela correta
        log("")
        log("⚠️ ATENÇÃO: Posicione a aplicação na tela")
        log("⏳ Aguardando 3 segundos para você posicionar...")
        esperar(3, "posicionamento")

        # ===================================================================
        # LOOP CONTÍNUO - Verifica a cada 30s se há itens para processar
        # ===================================================================
        ciclo_numero = 0
        primeiro_ciclo = True  # Flag para rastrear se é o primeiro ciclo

        while _rpa_running:
            ciclo_numero += 1

            log("")
            log("=" * 70)
            log(f"🔄 CICLO #{ciclo_numero}")
            log("=" * 70)

            # Buscar dados do Google Sheets
            log("🔍 Buscando dados do Google Sheets...")
            try:
                import google_sheets_inventario as gsheets
                dados = gsheets.buscar_dados_inventario(inventario, tipo_contagem, tipo_planilha)

                if dados:
                    log(f"✅ {len(dados)} itens encontrados para '{inventario}' (pendentes de processamento)")
                else:
                    log(f"⚠️ Nenhum item pendente encontrado para '{inventario}'")
                    log("ℹ️ Todos os itens já foram processados")
                    log("")
                    log("⏳ Aguardando 30 segundos para próxima verificação...")
                    esperar(30, "próxima verificação")
                    continue  # Voltar para início do loop
            except Exception as e:
                log(f"❌ Erro ao buscar dados do Google Sheets: {e}")
                log("⏳ Aguardando 30 segundos para tentar novamente...")
                esperar(30, "nova tentativa")
                continue

            # ===================================================================
            # ETAPAS 1-3: Apenas no PRIMEIRO CICLO
            # Nos ciclos seguintes, pula direto para processar itens
            # ===================================================================
            if primeiro_ciclo:
                # ===================================================================
                # ETAPA 1: Clicar no campo Nome e digitar inventário
                # ===================================================================
                log("")
                log("📍 [ETAPA 1/4] Clicando campo Nome...")

                if not clicar_imagem("input_nome.png", "campo Nome", timeout=10):
                    log("❌ Não foi possível localizar o campo Nome")
                    log("ℹ️ Certifique-se de que a imagem 'input_nome.png' existe na pasta elementos/")
                    log("⏳ Aguardando 30 segundos para tentar novamente...")
                    esperar(30, "nova tentativa")
                    continue

                esperar(0.5, "após clicar")

                # Digitar inventário
                digitar(inventario, f"inventário '{inventario}'")
                esperar(0.5, "após digitar inventário")

                # ===================================================================
                # ETAPA 2: Clicar botão Localizar
                # ===================================================================
                log("")
                log("📍 [ETAPA 2/4] Clicando botão Localizar...")

                if not clicar_imagem("botao_localizar.png", "botão Localizar", timeout=10):
                    log("❌ Não foi possível localizar o botão Localizar")
                    log("⏳ Aguardando 30 segundos para tentar novamente...")
                    esperar(30, "nova tentativa")
                    continue

                esperar(2, "processamento após Localizar")

                # ===================================================================
                # ETAPA 3: Clicar botão Sim no(s) popup(s)
                # ===================================================================
                log("")
                log("📍 [ETAPA 3/4] Procurando popup(s) Decisão...")

                # Tentar clicar "Sim" até 2 vezes (pode aparecer 2 popups)
                for tentativa in range(1, 3):
                    log(f"   Tentando popup {tentativa}/2...")

                    if clicar_imagem("botao_nao.png", f"botão Não (popup {tentativa})", confianca=0.7, timeout=3):
                        log(f"✅ Popup {tentativa} confirmado")
                        esperar(1, "após confirmar popup")
                    else:
                        log(f"   Popup {tentativa} não encontrado (ok se já passou)")
                        break

                primeiro_ciclo = False  # Marcar que já passou do primeiro ciclo

            else:
                # ===================================================================
                # CICLOS 2+: Clicar Limpar para garantir que está limpo
                # ===================================================================
                log("")
                log("📍 [CICLO 2+] Preparando para processar próximos itens...")
                log("   Clicando botão Limpar para garantir tela limpa...")

                if clicar_imagem("botao_limpar.png", "botão Limpar", confianca=0.7, timeout=5):
                    log("✅ Tela limpa - pronto para processar")
                    esperar(0.5, "após limpar")
                else:
                    log("⚠️ Botão Limpar não encontrado (ok se já está limpo)")

                log("   Iniciando processamento direto dos itens...")

            # ===================================================================
            # ETAPA 4: Processar cada item da planilha
            # ===================================================================
            log("")
            log("📍 [ETAPA 4/4] Processando itens da planilha...")
            log("")

            total_itens = len(dados)
            log(f"📊 Total de itens a processar: {total_itens}")
            log("")

            for index, item in enumerate(dados, start=1):
                check_stop()

                log(f"{'='*60}")
                log(f"📦 ITEM {index}/{total_itens}")
                log(f"{'='*60}")

                # Extrair dados do item
                item_id = item.get('ID', '')  # ID da coluna A
                etiqueta = item.get('Etiqueta', '')
                nova_etiqueta = item.get('Nova Etiqueta', '')
                item_valor = item.get('Item', '')
                subinventario = item.get('Sub Inventário', '') or item.get('Sub Inventario', '')
                endereco = item.get('Endereço', '') or item.get('Endereco', '')
                fisico = item.get('Físico', '') or item.get('Fisico', '')

                log(f"   ID: {item_id}")
                log(f"   Etiqueta: {etiqueta}")
                log(f"   Nova Etiqueta: {nova_etiqueta}")
                log(f"   Item: {item_valor}")
                log(f"   Sub Inventário: {subinventario}")
                log(f"   Endereço: {endereco}")
                log(f"   Físico: {fisico}")
                log(f"   É nova? {'SIM' if nova_etiqueta else 'NÃO'}")
                log("")

                # ===============================================================
                # VERIFICAÇÃO: Item já está sendo processado por outro robô?
                # ===============================================================
                status_atual = item.get('Status RPA', '')
                if status_atual and 'PROCESSANDO' in str(status_atual).upper():
                    log(f"⏭️ PULANDO item - Já está sendo processado: '{status_atual}'")
                    log(f"   Outro robô está trabalhando neste item")
                    continue

                # ===============================================================
                # MARCAR COMO "PROCESSANDO..." (LOCK/RESERVA DO ITEM)
                # Isso evita que outro robô pegue o mesmo item
                # ===============================================================
                if item_id:
                    # Rastrear item atual (para tratamento de parada manual)
                    global _item_atual_id
                    _item_atual_id = item_id

                    log(f"[{index}/{total_itens}] 🔒 Marcando item como PROCESSANDO...")
                    sucesso_lock = gsheets.atualizar_status_rpa(
                        item_id=item_id,
                        status="PROCESSANDO...",
                        tipo_contagem=tipo_contagem,
                        tipo_planilha=tipo_planilha,
                        robo_id=_robo_id
                    )
                    if sucesso_lock:
                        log(f"✅ Item reservado por {_robo_id}")
                    else:
                        log(f"⚠️ Não foi possível marcar item - pulando para segurança")
                        log(f"   Possível causa: Outro robô marcou este item simultaneamente")
                        _item_atual_id = None
                        continue
                else:
                    log(f"⚠️ ID não encontrado - não é possível reservar item")
                    continue

                # 4.1: Clicar campo Etiqueta e digitar
                try:
                    log(f"[{index}/{total_itens}] Clicando campo Etiqueta...")

                    if not clicar_imagem("input_etiqueta.png", "campo Etiqueta", timeout=10):
                        log(f"❌ Não foi possível localizar campo Etiqueta")
                        continue

                    esperar(0.5, "após clicar etiqueta")

                    # Digitar etiqueta
                    digitar(etiqueta, "etiqueta")
                    esperar(0.5, "após digitar etiqueta")

                except Exception as e:
                    log(f"❌ Erro ao preencher etiqueta: {e}")
                    continue

                # 4.2: NOVO FLUXO - Verificar campo Item após TAB
                try:
                    # TAB 1x para ir ao campo Item
                    pressionar_tab(1)
                    esperar(0.5, "após TAB para campo Item")

                    # Copiar conteúdo do campo Item (Ctrl+C)
                    item_atual = copiar_campo()

                    # Verificar se o campo Item tem algo preenchido
                    if item_atual and item_atual.strip() != '':
                        # Campo Item tem valor - verificar se é o esperado
                        item_esperado = str(item_valor).strip()
                        item_genesys = item_atual.strip()

                        if item_genesys == item_esperado:
                            # ============================================================
                            # ETIQUETA EXISTENTE - Item correto
                            # ============================================================
                            log(f"[{index}/{total_itens}] ✅ ETIQUETA EXISTENTE (Item correto: '{item_atual}')")

                            # BC1 vs BC2 - Número diferente de TABs
                            if tipo_planilha.lower() == "bc1":
                                # BC1: 2 TABs (um a menos)
                                log(f"[{index}/{total_itens}] Fluxo BC1: TAB → TAB → Quantidade → Salvar")
                                pressionar_tab(1)
                                pressionar_tab(1)
                            else:
                                # BC2: 3 TABs
                                log(f"[{index}/{total_itens}] Fluxo BC2: TAB → TAB → TAB → Quantidade → Salvar")
                                pressionar_tab(1)
                                pressionar_tab(1)
                                pressionar_tab(1)

                            # Digitar Quantidade (Físico)
                            digitar(fisico, "Quantidade (Físico)")
                            log(f"✅ Quantidade preenchida: {fisico}")

                        else:
                            # ============================================================
                            # 🚨 DIVERGÊNCIA DETECTADA - Item diferente do esperado
                            # ============================================================
                            log("")
                            log("=" * 70)
                            log("🚨 DIVERGÊNCIA DETECTADA - ITEM INCORRETO NO GENESYS")
                            log("=" * 70)
                            log(f"📋 Etiqueta: {etiqueta}")
                            log(f"❌ Item Esperado (Planilha): {item_esperado}")
                            log(f"⚠️ Item Encontrado (Genesys): {item_genesys}")
                            log("")
                            log("⚠️ O item cadastrado no Genesys não corresponde ao esperado!")
                            log("ℹ️ Verifique os dados antes de continuar.")
                            log("")
                            log("🛑 RPA INTERROMPIDO - Corrija a divergência e execute novamente")
                            log("=" * 70)
                            log("")

                            # Restaurar janela para o usuário ver o erro
                            try:
                                import tkinter as tk
                                # Se houver GUI rodando, restaurar janela
                                if _gui_log_callback:
                                    # A GUI vai mostrar a mensagem no log
                                    pass
                            except:
                                pass

                            # PARAR o RPA
                            raise Exception(f"DIVERGÊNCIA: Etiqueta '{etiqueta}' - Esperado item '{item_esperado}', mas Genesys tem '{item_genesys}'")

                    else:
                        # ============================================================
                        # ETIQUETA NOVA - Campo Item está vazio
                        # ============================================================
                        log(f"[{index}/{total_itens}] ⚠️ ETIQUETA NOVA (Item vazio)")
                        log(f"[{index}/{total_itens}] Fluxo: Item → TAB → SubInv → TAB → Endereço → TAB → UDM → TAB → Qtd → Salvar")

                        # Preencher Item
                        digitar(item_valor, "Item")
                        log(f"✅ Item preenchido: {item_valor}")

                        # TAB + Preencher Sub Inventário
                        pressionar_tab(1)
                        digitar(subinventario, "Sub Inventário")
                        log(f"✅ Sub Inventário preenchido: {subinventario}")

                        # TAB + Preencher Endereço
                        pressionar_tab(1)
                        digitar(endereco, "Endereço")
                        log(f"✅ Endereço preenchido: {endereco}")

                        # TAB + UDM (pular, não preencher)
                        pressionar_tab(1)
                        log(f"⏭️ UDM (pulado)")

                        # TAB + Preencher Quantidade (Físico)
                        pressionar_tab(1)
                        digitar(fisico, "Quantidade (Físico)")
                        log(f"✅ Quantidade preenchida: {fisico}")

                except Exception as e:
                    log(f"❌ Erro ao processar item: {e}")
                    # Se for erro de divergência, re-lançar para parar completamente
                    if "DIVERGÊNCIA" in str(e):
                        raise
                    continue

                # 4.3: Validação de Login Expirado
                try:
                    log(f"[{index}/{total_itens}] 🔍 Verificando se login do Oracle expirou...")

                    login_expirado = localizar_imagem("login_expirado.png", confianca=0.8, timeout=2)

                    if login_expirado:
                        # ============================================================
                        # 🚨 LOGIN EXPIRADO - PARAR ROBÔ
                        # ============================================================
                        log("")
                        log("=" * 70)
                        log("🚨 LOGIN DO ORACLE EXPIRADO!")
                        log("=" * 70)
                        log(f"📋 Etiqueta: {etiqueta}")
                        log("")
                        log("⚠️ A sessão do Oracle expirou e precisa fazer login novamente")
                        log("🛑 RPA INTERROMPIDO - Faça login no Oracle e execute novamente")
                        log("=" * 70)
                        log("")

                        # Marcar item como "Login Oracle Expirado" (para reprocessar)
                        if item_id:
                            log(f"Marcando item como 'Login Oracle Expirado'...")
                            gsheets.atualizar_status_rpa(
                                item_id=item_id,
                                status="Login Oracle Expirado",
                                tipo_contagem=tipo_contagem,
                                tipo_planilha=tipo_planilha,
                                robo_id=_robo_id
                            )
                            log(f"✅ Item marcado - poderá ser reprocessado após login")

                        # Parar o RPA completamente
                        raise Exception("LOGIN DO ORACLE EXPIRADO - Faça login e execute novamente")

                    else:
                        log(f"✅ Login OK - Continuando com salvamento")

                except Exception as e:
                    # Se for erro de login expirado, re-lançar para parar o RPA
                    if "LOGIN DO ORACLE EXPIRADO" in str(e):
                        raise
                    # Outros erros na verificação - apenas avisar e continuar
                    log(f"⚠️ Erro ao verificar login expirado: {e}")
                    log(f"   Continuando mesmo assim...")

                # 4.4: Clicar botão Salvar
                try:
                    log(f"[{index}/{total_itens}] Clicando botão Salvar...")

                    if not clicar_imagem("botao_salvar.png", "botão Salvar", confianca=0.7, timeout=5):
                        log(f"⚠️ Não conseguiu clicar no botão Salvar")
                        log(f"ℹ️ Continuando mesmo assim...")

                    esperar(8, "processamento após salvar")
                    log(f"✅ [{index}/{total_itens}] Item salvo")

                    # 4.5: Clicar botão Limpar
                    log(f"[{index}/{total_itens}] Clicando botão Limpar...")

                    if not clicar_imagem("botao_limpar.png", "botão Limpar", confianca=0.7, timeout=5):
                        log(f"⚠️ Não conseguiu clicar no botão Limpar")
                        log(f"ℹ️ Continuando mesmo assim...")

                    esperar(0.5, "após limpar")
                    log(f"✅ [{index}/{total_itens}] Item processado - pronto para próximo")

                    # 4.6: Atualizar status na planilha como CONCLUÍDO
                    if item_id:
                        log(f"[{index}/{total_itens}] Atualizando Status RPA na planilha...")
                        sucesso = gsheets.atualizar_status_rpa(
                            item_id=item_id,
                            status="PROCESSO CONCLUIDO",
                            tipo_contagem=tipo_contagem,
                            tipo_planilha=tipo_planilha,
                            robo_id=_robo_id
                        )
                        if sucesso:
                            log(f"✅ Status RPA atualizado na planilha (ID: {item_id}) por {_robo_id}")
                        else:
                            log(f"⚠️ Não foi possível atualizar Status RPA na planilha")
                    else:
                        log(f"⚠️ ID não encontrado - não foi possível atualizar planilha")

                    # Item concluído - limpar rastreamento
                    _item_atual_id = None

                except Exception as e:
                    log(f"⚠️ Aviso ao salvar: {e}")

                log("")

            log("=" * 60)
            log(f"✅ Processamento do ciclo #{ciclo_numero} concluído! {total_itens} itens processados")
            log("=" * 60)

            # Após processar todos os itens, aguardar 30s e verificar novamente
            log("")
            log("⏳ Aguardando 30 segundos para próxima verificação...")
            esperar(30, "próxima verificação")

        # Se saiu do loop, foi porque _rpa_running = False (usuário parou)
        log("")
        log("=" * 70)
        log("✅ RPA INVENTÁRIO - FINALIZADO")
        log("=" * 70)

    except KeyboardInterrupt:
        log("")
        log("=" * 70)
        log("🛑 ROBÔ INTERROMPIDO MANUALMENTE (ESC)")
        log("=" * 70)

        # Se estava processando um item, marcar para reprocessar
        if _item_atual_id:
            log(f"📋 Item em processamento quando parou: ID {_item_atual_id}")
            log(f"🔄 Marcando item para reprocessar...")

            try:
                import google_sheets_inventario as gsheets
                gsheets.atualizar_status_rpa(
                    item_id=_item_atual_id,
                    status="Interrompido - Reprocessar",
                    tipo_contagem=tipo_contagem,
                    tipo_planilha=tipo_planilha,
                    robo_id=_robo_id
                )
                log(f"✅ Item marcado como 'Interrompido - Reprocessar'")
                log(f"   Este item será reprocessado na próxima execução")
            except Exception as e:
                log(f"⚠️ Erro ao marcar item para reprocessar: {e}")

        log("")
        log("ℹ️ Para continuar processando, execute o robô novamente")
        log("=" * 70)

    except Exception as e:
        log("")
        log(f"❌ Erro durante execução: {e}")
        import traceback
        log(traceback.format_exc())

        # Se estava processando um item, marcar com erro
        if _item_atual_id:
            log(f"📋 Marcando item ID {_item_atual_id} com erro...")
            try:
                import google_sheets_inventario as gsheets
                gsheets.atualizar_status_rpa(
                    item_id=_item_atual_id,
                    status=f"Erro - Reprocessar",
                    tipo_contagem=tipo_contagem,
                    tipo_planilha=tipo_planilha,
                    robo_id=_robo_id
                )
                log(f"✅ Item marcado como 'Erro - Reprocessar'")
            except:
                pass

        raise
    finally:
        # Restaurar hibernação do PC
        restaurar_hibernacao()
        log("🔋 Hibernação do PC restaurada")

        # Remover listener do ESC e limpar recursos
        try:
            keyboard.unhook_all()
            log("🧹 Keyboard hooks removidos")
        except Exception as e:
            log(f"⚠️ Erro ao remover keyboard hooks: {e}")

        log("🏁 Limpeza finalizada")

if __name__ == "__main__":
    main()
