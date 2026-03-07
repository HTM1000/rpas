# -*- coding: utf-8 -*-
"""
validador_hibrido.py
====================
Sistema de validação híbrido para campos Oracle (substitui validação OCR).

Combina 3 técnicas para máxima confiabilidade:
1. Análise de Pixels - Detecta se campo está vazio ou preenchido
2. Clipboard - Lê valor exato do campo (Ctrl+A + Ctrl+C)
3. Detecção de Erros - Verifica imagens de erro (qtd_negativa, ErroProduto)

Vantagens sobre OCR:
- Não sofre com erros de reconhecimento (E vs &, 0 vs O, etc)
- Lê valor exato do campo sem ambiguidade
- Mais rápido que OCR complexo
- Combina verificação estrutural + semântica

Autor: Claude Code
Data: 2025-10-24
"""

import time
import pyautogui
import pyperclip
import numpy as np
from PIL import Image, ImageGrab
import os
import sys

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

# Threshold de pixels não-brancos para considerar campo preenchido
# IMPORTANTE: 2% estava pegando bordas/sombras como texto! Aumentado para 5%
THRESHOLD_PIXELS = 0.05  # 5% dos pixels devem ser não-brancos (mais rigoroso)

# Valor RGB considerado "branco" (pixels acima disso = vazios)
# IMPORTANTE: 240 pode estar deixando passar cinzas claros. Reduzido para 230
THRESHOLD_BRANCO = 230

# Delays para operações de clipboard (ms)
DELAY_CLIPBOARD_CLICK = 200
DELAY_CLIPBOARD_SELECT = 100
DELAY_CLIPBOARD_COPY = 200

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def gui_log(mensagem):
    """Log compatível com GUI (pode ser substituído externamente)"""
    print(mensagem)


def carregar_imagem_erro(nome_arquivo):
    """
    Carrega imagem de erro (compatível com .exe e script Python).

    Args:
        nome_arquivo: Nome do arquivo (ex: "qtd_negativa.png")

    Returns:
        str: Caminho completo da imagem ou None se não encontrado
    """
    if getattr(sys, 'frozen', False):
        # Executável: busca em _internal/informacoes/
        base_path = os.path.join(sys._MEIPASS, 'informacoes')
    else:
        # Script Python: busca em informacoes/
        base_path = os.path.join(os.path.dirname(__file__), 'informacoes')

    caminho = os.path.join(base_path, nome_arquivo)

    if os.path.exists(caminho):
        return caminho
    else:
        gui_log(f"⚠️ [VALIDADOR] Imagem não encontrada: {caminho}")
        return None


# ============================================================================
# ETAPA 1: VALIDAÇÃO POR ANÁLISE DE PIXELS
# ============================================================================

def validar_campo_preenchido(x, y, largura, altura, threshold=THRESHOLD_PIXELS):
    """
    Verifica se campo tem texto analisando densidade de pixels não-brancos.

    Técnica: Captura região do campo, converte para escala de cinza,
    conta quantos pixels são "escuros" (< 240). Se > threshold%, campo está preenchido.

    Args:
        x, y: Coordenadas do canto superior esquerdo
        largura, altura: Dimensões do campo
        threshold: % mínimo de pixels não-brancos para considerar preenchido

    Returns:
        tuple: (campo_preenchido: bool, percentual: float, detalhes: dict)
    """
    try:
        # Capturar campo
        img = ImageGrab.grab(bbox=(x, y, x + largura, y + altura))

        # Converter para escala de cinza
        img_gray = img.convert('L')
        img_array = np.array(img_gray)

        # Contar pixels não-brancos (texto/caracteres)
        pixels_nao_brancos = np.sum(img_array < THRESHOLD_BRANCO)
        total_pixels = img_array.size
        percentual = pixels_nao_brancos / total_pixels

        campo_preenchido = percentual > threshold

        detalhes = {
            "total_pixels": total_pixels,
            "pixels_nao_brancos": pixels_nao_brancos,
            "percentual": percentual,
            "threshold": threshold
        }

        return campo_preenchido, percentual, detalhes

    except Exception as e:
        gui_log(f"⚠️ [PIXELS] Erro ao analisar pixels: {e}")
        return False, 0.0, {"erro": str(e)}


# ============================================================================
# ETAPA 2: VALIDAÇÃO POR CLIPBOARD
# ============================================================================

def ler_campo_via_clipboard(x, y, timeout=1.0, tentar_triplo_clique=True):
    """
    Lê conteúdo exato do campo copiando para clipboard (Ctrl+A + Ctrl+C).

    Técnica:
    1. Salva clipboard atual
    2. Clica no campo
    3. Seleciona tudo (Ctrl+A OU triplo-clique para campos numéricos)
    4. Copia (Ctrl+C)
    5. Lê clipboard
    6. Restaura clipboard original

    Args:
        x, y: Coordenadas do campo
        timeout: Tempo máximo de espera (segundos)
        tentar_triplo_clique: Se True, tenta triplo-clique antes de Ctrl+A (melhor para números)

    Returns:
        str: Conteúdo do campo ou "" se erro
    """
    clipboard_backup = ""

    try:
        # 🔧 CORREÇÃO: Verificar se RPA está rodando antes de iniciar
        # Importar dinamicamente para evitar dependência circular
        try:
            import main_ciclo
            if not main_ciclo._rpa_running:
                gui_log("   ⚠️ [CLIPBOARD] RPA parado, abortando leitura")
                return ""
        except:
            pass  # Se não conseguir importar, continua normalmente

        # Salvar clipboard atual
        clipboard_backup = pyperclip.paste()

        # Limpar clipboard
        pyperclip.copy("")

        # Clicar no campo
        pyautogui.click(x, y)
        time.sleep(DELAY_CLIPBOARD_CLICK / 1000.0)

        # 🔧 CORREÇÃO: Tentar TRIPLO-CLIQUE primeiro (melhor para campos alinhados à direita)
        # Triplo-clique seleciona todo o conteúdo sem espaços extras
        valor = ""

        if tentar_triplo_clique:
            try:
                # Triplo-clique para selecionar tudo
                pyautogui.click(x, y, clicks=3, interval=0.05)
                time.sleep(DELAY_CLIPBOARD_SELECT / 1000.0)

                # Copiar
                pyautogui.hotkey('ctrl', 'c')
                time.sleep(DELAY_CLIPBOARD_COPY / 1000.0)

                # Ler clipboard
                valor = pyperclip.paste().strip()

                # Se conseguiu ler algo, retorna
                if valor:
                    gui_log(f"   📋 [TRIPLO-CLIQUE] Lido: '{valor}'")
                    return valor
            except:
                pass

        # Fallback: Usar Ctrl+A (método original)
        # 🔧 Verificar novamente se RPA foi parado
        try:
            import main_ciclo
            if not main_ciclo._rpa_running:
                gui_log("   ⚠️ [CLIPBOARD] RPA parado durante fallback")
                return ""
        except:
            pass

        pyperclip.copy("")  # Limpar novamente
        pyautogui.click(x, y)  # Clicar novamente
        time.sleep(DELAY_CLIPBOARD_CLICK / 1000.0)

        # Selecionar tudo
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(DELAY_CLIPBOARD_SELECT / 1000.0)

        # Copiar
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(DELAY_CLIPBOARD_COPY / 1000.0)

        # Ler clipboard
        valor = pyperclip.paste().strip()
        gui_log(f"   📋 [CTRL+A] Lido: '{valor}'")

        return valor

    except Exception as e:
        gui_log(f"⚠️ [CLIPBOARD] Erro ao ler campo: {e}")
        return ""

    finally:
        # Restaurar clipboard (com proteção contra erro)
        try:
            pyperclip.copy(clipboard_backup)
        except:
            pass


def validar_campo_clipboard(x, y, valor_esperado, nome_campo="Campo", normalizar=True):
    """
    Valida campo Oracle comparando valor via clipboard.

    Args:
        x, y: Coordenadas do campo
        valor_esperado: Valor que deveria estar no campo
        nome_campo: Nome do campo (para logs)
        normalizar: Se True, remove espaços e converte para maiúsculas

    Returns:
        tuple: (sucesso: bool, valor_lido: str, detalhes: dict)
    """
    try:
        # Ler valor do campo
        valor_lido = ler_campo_via_clipboard(x, y)

        if normalizar:
            # Normalizar valores (maiúsculas, sem espaços)
            valor_lido_norm = valor_lido.upper().strip().replace(" ", "")
            valor_esperado_norm = str(valor_esperado).upper().strip().replace(" ", "")
        else:
            valor_lido_norm = valor_lido.strip()
            valor_esperado_norm = str(valor_esperado).strip()

        # 🔧 CORREÇÃO: Para campos numéricos (quantidade, etc), fazer comparação numérica
        # Isso resolve problemas com alinhamento à direita e formatação diferente
        eh_campo_quantidade = "QUANT" in nome_campo.upper() or nome_campo.upper() == "QUANTIDADE"

        if eh_campo_quantidade:
            try:
                # Tentar converter ambos para números para comparação
                # Remove vírgulas, pontos de milhar, etc
                valor_lido_num = valor_lido_norm.replace(",", "").replace(".", "")
                valor_esperado_num = str(valor_esperado_norm).replace(",", "").replace(".", "")

                # Comparar como números
                if valor_lido_num.isdigit() and valor_esperado_num.isdigit():
                    sucesso = int(valor_lido_num) == int(valor_esperado_num)
                    gui_log(f"   🔢 [NUMÉRICO] Comparação: {int(valor_lido_num)} == {int(valor_esperado_num)} → {sucesso}")
                else:
                    # Fallback: comparação de string
                    sucesso = valor_lido_norm == valor_esperado_norm
                    gui_log(f"   📝 [STRING] Comparação: '{valor_lido_norm}' == '{valor_esperado_norm}' → {sucesso}")
            except:
                # Se conversão falhar, usa comparação de string padrão
                sucesso = valor_lido_norm == valor_esperado_norm
                gui_log(f"   ⚠️ [FALLBACK] Comparação string: '{valor_lido_norm}' == '{valor_esperado_norm}' → {sucesso}")
        else:
            sucesso = valor_lido_norm == valor_esperado_norm

        detalhes = {
            "valor_lido": valor_lido,
            "valor_esperado": valor_esperado,
            "valor_lido_norm": valor_lido_norm,
            "valor_esperado_norm": valor_esperado_norm,
            "normalizado": normalizar,
            "eh_campo_quantidade": eh_campo_quantidade
        }

        return sucesso, valor_lido, detalhes

    except Exception as e:
        gui_log(f"⚠️ [CLIPBOARD] Erro na validação: {e}")
        return False, "", {"erro": str(e)}


# ============================================================================
# ETAPA 3: DETECÇÃO DE ERROS VISUAIS
# ============================================================================

def detectar_erro_oracle(confidence=0.7):
    """
    Detecta erros visuais do Oracle usando template matching.

    Verifica se aparecem as imagens de erro conhecidas:
    - qtd_negativa.png: Erro de quantidade negativa
    - ErroProduto.png: Produto inválido/não encontrado

    Args:
        confidence: Confiança mínima para considerar match (0.0-1.0)

    Returns:
        tuple: (erro_detectado: bool, tipo_erro: str, posicao: tuple ou None)
    """
    try:
        # Verificar qtd_negativa.png
        img_qtd_negativa = carregar_imagem_erro("qtd_negativa.png")
        if img_qtd_negativa:
            try:
                pos_qtd = pyautogui.locateOnScreen(img_qtd_negativa, confidence=confidence)
                if pos_qtd:
                    gui_log(f"🛑 [ERRO] Quantidade negativa detectada em {pos_qtd}")
                    return True, "QTD_NEGATIVA", pos_qtd
            except pyautogui.ImageNotFoundException:
                pass

        # Verificar ErroProduto.png
        img_erro_produto = carregar_imagem_erro("ErroProduto.png")
        if img_erro_produto:
            try:
                pos_erro = pyautogui.locateOnScreen(img_erro_produto, confidence=confidence)
                if pos_erro:
                    gui_log(f"🛑 [ERRO] Produto inválido detectado em {pos_erro}")
                    return True, "PRODUTO_INVALIDO", pos_erro
            except pyautogui.ImageNotFoundException:
                pass

        # Nenhum erro detectado
        return False, "", None

    except Exception as e:
        gui_log(f"⚠️ [DETECÇÃO] Erro ao verificar imagens: {e}")
        return False, "ERRO_DETECCAO", None


# ============================================================================
# VALIDAÇÃO HÍBRIDA PRINCIPAL
# ============================================================================

def validar_campo_oracle_hibrido(
    x, y, largura, altura,
    valor_esperado,
    nome_campo="Campo",
    validar_conteudo=True,
    verificar_erros=True
):
    """
    Validação híbrida usando CLIPBOARD como método principal.

    ETAPA 1: Clipboard (Ctrl+C) - Verifica se campo tem conteúdo
    ETAPA 2: Detecção de Erros (imagens de erro) - OPCIONAL

    Args:
        x, y: Coordenadas do canto superior esquerdo do campo
        largura, altura: Dimensões do campo
        valor_esperado: Valor que deveria estar no campo
        nome_campo: Nome do campo (para logs)
        validar_conteudo: Se True, compara valor | Se False, só verifica se preenchido
        verificar_erros: Se True, verifica imagens de erro (Etapa 3)

    Returns:
        tuple: (sucesso: bool, tipo_resultado: str, detalhes: dict)

        Tipos de resultado:
        - "OK": Validação passou em todas as etapas
        - "CAMPO_VAZIO": Campo não tem conteúdo (clipboard vazio)
        - "VALOR_ERRADO": Valor diverge do esperado
        - "QTD_NEGATIVA": Erro Oracle de quantidade negativa
        - "PRODUTO_INVALIDO": Erro Oracle de produto inválido
        - "ERRO_VALIDACAO": Erro durante validação
    """
    detalhes = {
        "campo": nome_campo,
        "coordenadas": (x, y, largura, altura),
        "valor_esperado": valor_esperado,
        "etapas": {}
    }

    gui_log(f"🔍 [HÍBRIDO] Iniciando validação: {nome_campo}")
    gui_log(f"   📍 Posição: ({x}, {y}) | Tamanho: {largura}x{altura}")

    # ────────────────────────────────────────────────────────────────────────
    # ETAPA 1: Ler campo via Clipboard (Ctrl+C)
    # ────────────────────────────────────────────────────────────────────────
    gui_log(f"   [1/2] Lendo campo via clipboard (Ctrl+C)...")

    # Calcular centro do campo para clicar
    centro_x = x + largura // 2
    centro_y = y + altura // 2

    # Ler valor do campo
    valor_lido = ler_campo_via_clipboard(centro_x, centro_y)

    # Verificar se campo está vazio
    if not valor_lido or valor_lido.strip() == "":
        gui_log(f"   ❌ Campo VAZIO! Clipboard retornou: '{valor_lido}'")
        detalhes["etapas"]["clipboard"] = {
            "valor_lido": valor_lido,
            "campo_vazio": True
        }
        return False, "CAMPO_VAZIO", detalhes

    gui_log(f"   ✅ Campo PREENCHIDO! Valor lido: '{valor_lido}'")

    # Se validar_conteudo=True, compara valores
    if validar_conteudo:
        gui_log(f"   [1.1] Comparando valor lido com esperado...")

        # Normalizar valores
        valor_lido_norm = valor_lido.upper().strip().replace(" ", "")
        valor_esperado_norm = str(valor_esperado).upper().strip().replace(" ", "")

        # Verificar se é campo numérico
        eh_campo_quantidade = "QUANT" in nome_campo.upper()

        if eh_campo_quantidade:
            try:
                valor_lido_num = valor_lido_norm.replace(",", "").replace(".", "")
                valor_esperado_num = str(valor_esperado_norm).replace(",", "").replace(".", "")

                if valor_lido_num.isdigit() and valor_esperado_num.isdigit():
                    sucesso = int(valor_lido_num) == int(valor_esperado_num)
                    gui_log(f"      🔢 [NUMÉRICO] {int(valor_lido_num)} == {int(valor_esperado_num)} → {sucesso}")
                else:
                    sucesso = valor_lido_norm == valor_esperado_norm
                    gui_log(f"      📝 [STRING] '{valor_lido_norm}' == '{valor_esperado_norm}' → {sucesso}")
            except:
                sucesso = valor_lido_norm == valor_esperado_norm
        else:
            sucesso = valor_lido_norm == valor_esperado_norm
            gui_log(f"      📝 '{valor_lido_norm}' == '{valor_esperado_norm}' → {sucesso}")

        detalhes["etapas"]["clipboard"] = {
            "valor_lido": valor_lido,
            "valor_esperado": valor_esperado,
            "valor_lido_norm": valor_lido_norm,
            "valor_esperado_norm": valor_esperado_norm,
            "sucesso": sucesso
        }

        if not sucesso:
            gui_log(f"   ❌ VALORES DIFERENTES!")
            return False, "VALOR_ERRADO", detalhes

        gui_log(f"   ✅ Valores correspondem!")
    else:
        gui_log(f"   [1.1] Validação de conteúdo desabilitada - qualquer valor aceito")
        detalhes["etapas"]["clipboard"] = {
            "valor_lido": valor_lido,
            "campo_vazio": False,
            "validacao_conteudo": False
        }

    # ────────────────────────────────────────────────────────────────────────
    # ETAPA 2: Erro Oracle? (Detecção Visual) - OPCIONAL
    # ────────────────────────────────────────────────────────────────────────
    if verificar_erros:
        gui_log(f"   [2/2] Verificando erros Oracle...")

        erro_detectado, tipo_erro, posicao = detectar_erro_oracle()
        detalhes["etapas"]["deteccao_erros"] = {
            "erro_detectado": erro_detectado,
            "tipo_erro": tipo_erro,
            "posicao": posicao
        }

        if erro_detectado:
            gui_log(f"   🛑 ERRO ORACLE: {tipo_erro}")
            return False, tipo_erro, detalhes

        gui_log(f"   ✅ Sem erros detectados")
    else:
        gui_log(f"   [2/2] Pulando detecção de erros (verificar_erros=False)")

    # ────────────────────────────────────────────────────────────────────────
    # SUCESSO!
    # ────────────────────────────────────────────────────────────────────────
    gui_log(f"   ✅✅ [{nome_campo}] Validação completa OK!")
    return True, "OK", detalhes


def validar_campos_oracle_completo(coords, item, quantidade, referencia, sub_o, end_o, sub_d, end_d):
    """
    Valida todos os campos do formulário Oracle de uma vez.

    Substitui a função validar_campos_oracle_ocr() do main_ciclo.py.

    Args:
        coords: Dicionário com coordenadas dos campos (do config.json)
        item, quantidade, referencia, sub_o, end_o, sub_d, end_d: Valores esperados

    Returns:
        tuple: (validacao_ok: bool, tipo_erro: str)
    """
    gui_log("═══════════════════════════════════════════════════════════")
    gui_log("🔍 [VALIDAÇÃO HÍBRIDA] Iniciando validação completa")
    gui_log("═══════════════════════════════════════════════════════════")

    # 📊 MOSTRAR VALORES ESPERADOS DA PLANILHA
    gui_log("")
    gui_log("📊 VALORES ESPERADOS (da planilha Google Sheets):")
    gui_log(f"   Item: '{item}'")
    gui_log(f"   Quantidade: '{quantidade}'")
    gui_log(f"   Referência: '{referencia}'")
    gui_log(f"   Subinvent. (origem): '{sub_o}'")
    gui_log(f"   Endereço (origem): '{end_o}'")
    gui_log(f"   Para Subinv. (destino): '{sub_d}'")
    gui_log(f"   Para Loc. (destino): '{end_d}'")
    gui_log("")

    # Detectar tipo de referência
    eh_cod = referencia and str(referencia).upper().strip().startswith("COD")

    # ═══════════════════════════════════════════════════════════════════════
    # REGRA DE VALIDAÇÃO:
    # - SEMPRE compara: Item, Subinvent.(origem), Endereço(origem), Quantidade, Referência
    # - Para Subinv. e Para Loc.: só compara se for MOV (não compara se for COD)
    # ═══════════════════════════════════════════════════════════════════════

    if eh_cod:
        gui_log("📋 Referência COD detectada")
        gui_log("   ⚙️ REGRA: Compara valores de Item, Sub.Origem, End.Origem, Qtd, Ref")
        gui_log("   ⚙️ REGRA: NÃO compara Para Subinv. e Para Loc. (preenchidos pelo Oracle)")

        # Para COD: compara campos de origem, NÃO compara destino
        # Formato: (nome, coordenadas, valor_esperado, comparar_valor)
        campos_validar = [
            ("Item", coords["campo_item"], item, True),
            ("Subinvent.", coords["campo_sub_o"], sub_o, True),
            ("Endereço", coords["campo_end_o"], end_o, True),
            ("Quantidade", coords["campo_quantidade"], quantidade, True),
            ("Referência", coords["campo_referencia"], referencia, True),
            ("Para Subinv.", coords["campo_sub_d"], sub_d, False),  # NÃO compara (Oracle preenche)
            ("Para Loc.", coords["campo_end_d"], end_d, False),     # NÃO compara (Oracle preenche)
        ]
    else:
        gui_log("📋 Referência MOV/OUTRO detectada")
        gui_log("   ⚙️ REGRA: Compara valores de TODOS os campos (origem + destino)")

        # Para MOV/OUTRO: compara TODOS os campos
        # Formato: (nome, coordenadas, valor_esperado, comparar_valor)
        campos_validar = [
            ("Item", coords["campo_item"], item, True),
            ("Subinvent.", coords["campo_sub_o"], sub_o, True),
            ("Endereço", coords["campo_end_o"], end_o, True),
            ("Para Subinv.", coords["campo_sub_d"], sub_d, True),   # Compara (digitado pelo RPA)
            ("Para Loc.", coords["campo_end_d"], end_d, True),      # Compara (digitado pelo RPA)
            ("Quantidade", coords["campo_quantidade"], quantidade, True),
            ("Referência", coords["campo_referencia"], referencia, True),
        ]

    gui_log("")
    gui_log("─" * 60)
    gui_log("🔎 INICIANDO VALIDAÇÃO CAMPO POR CAMPO:")
    gui_log("─" * 60)

    # Validar cada campo
    erros = []
    erros_detalhados = []
    campos_validados_ok = []

    for idx, (nome, coord, valor, comparar_valor) in enumerate(campos_validar, 1):
        # 🔧 CORREÇÃO: Verificar se RPA foi parado
        try:
            import main_ciclo
            if not main_ciclo._rpa_running:
                gui_log("🛑 RPA PARADO - Interrompendo validação")
                return False, "RPA_PARADO"
        except:
            pass

        x, y, largura, altura = coord

        gui_log("")
        gui_log(f"━━━ [{idx}/{len(campos_validar)}] CAMPO: {nome} ━━━")
        gui_log(f"📝 Valor esperado (planilha): '{valor}'")
        if comparar_valor:
            gui_log(f"🔍 MODO: Comparar valor digitado com valor esperado")
        else:
            gui_log(f"🔍 MODO: Apenas verificar se está preenchido (sem comparar)")
        gui_log(f"📍 Coordenadas: ({x}, {y}) | Tamanho: {largura}x{altura}")

        # Primeiro: verificar se campo está preenchido
        sucesso, tipo, detalhes = validar_campo_oracle_hibrido(
            x, y, largura, altura,
            valor_esperado=valor,
            nome_campo=nome,
            validar_conteudo=False,  # Primeiro só verifica se está preenchido
            verificar_erros=False
        )

        if not sucesso:
            # Campo vazio ou erro
            if tipo == "CAMPO_VAZIO":
                clipboard_info = detalhes.get("etapas", {}).get("clipboard", {})
                valor_clipboard = clipboard_info.get("valor_lido", "")

                gui_log(f"❌ ERRO: Campo está VAZIO!")
                gui_log(f"   📋 Clipboard retornou: '{valor_clipboard}'")
                gui_log(f"   ⚠️ Campo obrigatório não foi preenchido")
                erro_detalhado = f"{nome}: CAMPO_VAZIO (clipboard: '{valor_clipboard}')"
            else:
                gui_log(f"❌ ERRO: {tipo}")
                erro_detalhado = f"{nome}: {tipo}"

            erros.append(f"{nome} ({tipo})")
            erros_detalhados.append(erro_detalhado)
        else:
            # Campo está preenchido - extrair valor lido
            clipboard_info = detalhes.get("etapas", {}).get("clipboard", {})
            valor_lido = clipboard_info.get("valor_lido", "")

            gui_log(f"✅ Campo PREENCHIDO")
            gui_log(f"   📋 Valor lido: '{valor_lido}'")

            # Se deve comparar valor, fazer a comparação
            if comparar_valor:
                # Normalizar valores para comparação
                valor_lido_norm = valor_lido.upper().strip().replace(" ", "")
                valor_esperado_norm = str(valor).upper().strip().replace(" ", "")

                # Comparação especial para quantidade (numérica)
                if "QUANT" in nome.upper():
                    try:
                        # Remover formatação numérica
                        val_lido_num = valor_lido_norm.replace(",", "").replace(".", "").lstrip("0") or "0"
                        val_esp_num = valor_esperado_norm.replace(",", "").replace(".", "").replace("-", "").lstrip("0") or "0"
                        valores_iguais = val_lido_num == val_esp_num
                        gui_log(f"   🔢 Comparação numérica: '{val_lido_num}' == '{val_esp_num}' → {valores_iguais}")
                    except:
                        valores_iguais = valor_lido_norm == valor_esperado_norm
                else:
                    valores_iguais = valor_lido_norm == valor_esperado_norm

                if valores_iguais:
                    gui_log(f"   ✅ VALOR CORRETO! '{valor_lido}' == '{valor}'")
                    campos_validados_ok.append(nome)
                else:
                    gui_log(f"   ❌ VALOR DIFERENTE!")
                    gui_log(f"      Esperado: '{valor}'")
                    gui_log(f"      Lido:     '{valor_lido}'")
                    erro_detalhado = f"{nome}: VALOR_DIFERENTE (esperado: '{valor}', lido: '{valor_lido}')"
                    erros.append(f"{nome} (VALOR_DIFERENTE)")
                    erros_detalhados.append(erro_detalhado)
            else:
                # Não precisa comparar, só estar preenchido já é suficiente
                gui_log(f"   ✅ OK (valor não comparado)")
                campos_validados_ok.append(nome)

    gui_log("")
    gui_log("─" * 60)
    gui_log("📊 RESUMO DA VALIDAÇÃO:")
    gui_log("─" * 60)

    # Log dos campos validados com sucesso
    if campos_validados_ok:
        gui_log(f"✅ Campos validados OK ({len(campos_validados_ok)}):")
        for campo in campos_validados_ok:
            gui_log(f"   • {campo}")

    # Verificar erros globais Oracle
    gui_log("")
    gui_log("🔍 Verificando erros visuais do Oracle...")
    erro_detectado, tipo_erro, _ = detectar_erro_oracle()

    if erro_detectado:
        gui_log(f"🛑 ERRO ORACLE GLOBAL: {tipo_erro}")
        gui_log("═══════════════════════════════════════════════════════════")
        return False, tipo_erro

    gui_log("✅ Sem erros visuais detectados")

    # Retornar resultado
    if erros:
        gui_log("")
        gui_log(f"❌ VALIDAÇÃO FALHOU! {len(erros)} campo(s) com erro:")
        for idx, erro_det in enumerate(erros_detalhados, 1):
            gui_log(f"{idx}. {erro_det}")

        # Criar tipo de erro resumido
        tipo_erro_resumido = " + ".join(erros[:3])  # Máximo 3 campos no resumo
        if len(erros) > 3:
            tipo_erro_resumido += f" (+{len(erros)-3} outros)"

        gui_log("")
        gui_log("🧹 Formulário será LIMPO com F6 para reprocessamento")
        gui_log("═══════════════════════════════════════════════════════════")
        return False, tipo_erro_resumido

    gui_log("")
    gui_log("✅✅✅ TODOS OS CAMPOS VALIDADOS COM SUCESSO!")
    gui_log("═══════════════════════════════════════════════════════════")
    return True, ""


# ============================================================================
# MODO DE TESTE
# ============================================================================

if __name__ == "__main__":
    """
    Teste standalone do validador híbrido.

    Uso:
        python validador_hibrido.py
    """
    print("=" * 60)
    print("TESTE DO VALIDADOR HÍBRIDO")
    print("=" * 60)

    # Teste de análise de pixels
    print("\n1. Teste de Análise de Pixels")
    print("   Clique em um campo do Oracle em 3 segundos...")
    time.sleep(3)

    # Capturar posição do mouse
    x, y = pyautogui.position()
    print(f"   Posição capturada: ({x}, {y})")

    # Validar campo (exemplo: 200x30 pixels)
    preenchido, percentual, detalhes = validar_campo_preenchido(x-100, y-15, 200, 30)
    print(f"   Campo preenchido: {preenchido}")
    print(f"   Percentual pixels: {percentual:.2%}")
    print(f"   Detalhes: {detalhes}")

    # Teste de clipboard
    print("\n2. Teste de Clipboard")
    print("   Clique em um campo com texto em 3 segundos...")
    time.sleep(3)

    x, y = pyautogui.position()
    valor = ler_campo_via_clipboard(x, y)
    print(f"   Valor lido: '{valor}'")

    # Teste de detecção de erros
    print("\n3. Teste de Detecção de Erros")
    erro, tipo, pos = detectar_erro_oracle()
    print(f"   Erro detectado: {erro}")
    print(f"   Tipo: {tipo}")
    print(f"   Posição: {pos}")

    print("\n" + "=" * 60)
    print("TESTES CONCLUÍDOS")
    print("=" * 60)
