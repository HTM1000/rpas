# -*- coding: utf-8 -*-
"""
TESTE DE SIMULAÇÃO OCR - SEM CTRL+S
Simula o preenchimento dos campos e testa a validação OCR
sem executar o Ctrl+S (para não salvar dados no Oracle)
"""

import time
import pyautogui
from pathlib import Path
import sys
import os

# Importar Google Sheets
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Importar OCR
try:
    import pytesseract
    from PIL import Image, ImageGrab
    PYTESSERACT_DISPONIVEL = True
    print("✅ pytesseract importado com sucesso")

    # Configurar caminho do tesseract (MESMA LÓGICA DO MAIN_CICLO.PY)
    tesseract_configurado = False

    # 1. PRIORIDADE: Tesseract na pasta local (junto com o .exe ou script)
    if getattr(sys, 'frozen', False):
        # Executável: procurar na pasta do .exe
        local_tesseract = os.path.join(os.path.dirname(sys.executable), 'tesseract', 'tesseract.exe')
    else:
        # Desenvolvimento: procurar na pasta do script
        local_tesseract = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tesseract', 'tesseract.exe')

    if os.path.exists(local_tesseract):
        pytesseract.pytesseract.tesseract_cmd = local_tesseract
        print(f"✅ Tesseract LOCAL encontrado: {local_tesseract}")
        tesseract_configurado = True

    # 2. Fallback: Tesseract instalado no sistema
    if not tesseract_configurado:
        # Tentar localização padrão do instalador
        default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(default_path):
            pytesseract.pytesseract.tesseract_cmd = default_path
            print(f"✅ Tesseract SISTEMA encontrado: {default_path}")
            tesseract_configurado = True
        else:
            # Tentar localizar no PATH
            import shutil
            tesseract_cmd = shutil.which('tesseract')
            if tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                print(f"✅ Tesseract PATH encontrado: {tesseract_cmd}")
                tesseract_configurado = True

    if not tesseract_configurado:
        print("⚠️ Tesseract-OCR não encontrado!")
        print("⚠️ O teste precisa do Tesseract para funcionar.")
        print("")
        print("Opções:")
        print("1. Instale o Tesseract: instalar_tesseract.bat")
        print("2. Ou copie a pasta 'tesseract' para junto deste script")
        PYTESSERACT_DISPONIVEL = False
        sys.exit(1)

except ImportError as e:
    PYTESSERACT_DISPONIVEL = False
    print(f"❌ pytesseract não disponível: {e}")
    print("Execute: pip install pytesseract")
    sys.exit(1)

# =================== CONFIGURAÇÕES ===================
PLANILHA_TESTE_ID = "147AN4Kn11T2qGyzTQgdqJ0QfSIt9TATEi0lw9zwMnpY"
SHEET_NAME = "Separação"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Coordenadas dos campos no Oracle (mesmas do main_ciclo.py)
coords = {
    "item": (101, 156),
    "sub_origem": (257, 159),
    "end_origem": (335, 159),
    "sub_destino": (485, 159),
    "end_destino": (553, 159),
    "quantidade": (672, 159),
    "Referencia": (768, 159),
}

# =================== FUNÇÕES OCR ===================
def verificar_campo_ocr(x, y, largura, altura, valor_esperado, nome_campo="Campo"):
    """Captura região da tela e usa OCR para verificar se o valor está correto"""
    if not PYTESSERACT_DISPONIVEL:
        print(f"⚠️ [OCR] pytesseract não disponível, pulando verificação de {nome_campo}")
        return (True, "", 0.0)

    try:
        # Capturar região da tela
        screenshot = ImageGrab.grab(bbox=(x, y, x + largura, y + altura))

        # Salvar screenshot para debug (opcional)
        screenshot.save(f"debug_ocr_{nome_campo}.png")

        # Aplicar OCR
        texto_lido = pytesseract.image_to_string(screenshot, config='--psm 7').strip()

        # Normalizar textos para comparação
        texto_lido_norm = texto_lido.replace(" ", "").upper()
        valor_esperado_norm = str(valor_esperado).replace(" ", "").upper()

        # Verificar similaridade
        if texto_lido_norm == valor_esperado_norm:
            print(f"✅ [OCR] {nome_campo}: '{texto_lido}' == '{valor_esperado}' (CORRETO)")
            return (True, texto_lido, 1.0)
        else:
            # Calcular similaridade parcial
            if len(valor_esperado_norm) > 0:
                caracteres_corretos = sum(1 for a, b in zip(texto_lido_norm, valor_esperado_norm) if a == b)
                confianca = caracteres_corretos / len(valor_esperado_norm)
            else:
                confianca = 0.0

            print(f"⚠️ [OCR] {nome_campo}: Esperado '{valor_esperado}', Lido '{texto_lido}' (Similaridade: {confianca*100:.1f}%)")

            # Se similaridade for > 80%, considera aceitável
            if confianca >= 0.8:
                print(f"✅ [OCR] {nome_campo}: Similaridade aceitável ({confianca*100:.1f}% >= 80%)")
                return (True, texto_lido, confianca)
            else:
                return (False, texto_lido, confianca)

    except Exception as e:
        print(f"⚠️ [OCR] Erro ao verificar {nome_campo}: {e}")
        return (True, "", 0.0)

def validar_campos_oracle_ocr(coords, item, quantidade, referencia, sub_o, end_o, sub_d, end_d):
    """Valida todos os campos do Oracle usando OCR"""
    print("\n🔍 [OCR] Iniciando validação visual dos campos...")

    # Dimensões padrão dos campos
    LARGURA_CAMPO = 100
    ALTURA_CAMPO = 20

    erros = []
    resultados = []

    # Validar Item
    sucesso, texto, conf = verificar_campo_ocr(
        coords["item"][0], coords["item"][1],
        LARGURA_CAMPO, ALTURA_CAMPO,
        item, "Item"
    )
    resultados.append({"campo": "Item", "sucesso": sucesso, "esperado": item, "lido": texto, "confianca": conf})
    if not sucesso:
        erros.append(f"Item (esperado: {item}, lido: {texto})")

    # Validar Quantidade
    sucesso, texto, conf = verificar_campo_ocr(
        coords["quantidade"][0], coords["quantidade"][1],
        80, ALTURA_CAMPO,
        quantidade, "Quantidade"
    )
    resultados.append({"campo": "Quantidade", "sucesso": sucesso, "esperado": quantidade, "lido": texto, "confianca": conf})
    if not sucesso:
        erros.append(f"Quantidade (esperado: {quantidade}, lido: {texto})")

    # Validar Referência
    sucesso, texto, conf = verificar_campo_ocr(
        coords["Referencia"][0], coords["Referencia"][1],
        80, ALTURA_CAMPO,
        referencia, "Referência"
    )
    resultados.append({"campo": "Referência", "sucesso": sucesso, "esperado": referencia, "lido": texto, "confianca": conf})
    if not sucesso:
        erros.append(f"Referência (esperado: {referencia}, lido: {texto})")

    # Validar Sub.Origem
    sucesso, texto, conf = verificar_campo_ocr(
        coords["sub_origem"][0], coords["sub_origem"][1],
        LARGURA_CAMPO, ALTURA_CAMPO,
        sub_o, "Sub.Origem"
    )
    resultados.append({"campo": "Sub.Origem", "sucesso": sucesso, "esperado": sub_o, "lido": texto, "confianca": conf})
    if not sucesso:
        erros.append(f"Sub.Origem (esperado: {sub_o}, lido: {texto})")

    # Validar End.Origem
    sucesso, texto, conf = verificar_campo_ocr(
        coords["end_origem"][0], coords["end_origem"][1],
        LARGURA_CAMPO, ALTURA_CAMPO,
        end_o, "End.Origem"
    )
    resultados.append({"campo": "End.Origem", "sucesso": sucesso, "esperado": end_o, "lido": texto, "confianca": conf})
    if not sucesso:
        erros.append(f"End.Origem (esperado: {end_o}, lido: {texto})")

    # Se não é COD, validar destino
    if not str(referencia).strip().upper().startswith("COD"):
        sucesso, texto, conf = verificar_campo_ocr(
            coords["sub_destino"][0], coords["sub_destino"][1],
            LARGURA_CAMPO, ALTURA_CAMPO,
            sub_d, "Sub.Destino"
        )
        resultados.append({"campo": "Sub.Destino", "sucesso": sucesso, "esperado": sub_d, "lido": texto, "confianca": conf})
        if not sucesso:
            erros.append(f"Sub.Destino (esperado: {sub_d}, lido: {texto})")

        sucesso, texto, conf = verificar_campo_ocr(
            coords["end_destino"][0], coords["end_destino"][1],
            LARGURA_CAMPO, ALTURA_CAMPO,
            end_d, "End.Destino"
        )
        resultados.append({"campo": "End.Destino", "sucesso": sucesso, "esperado": end_d, "lido": texto, "confianca": conf})
        if not sucesso:
            erros.append(f"End.Destino (esperado: {end_d}, lido: {texto})")

    # Resultado final
    if erros:
        print(f"\n❌ [OCR] Validação visual FALHOU. Erros encontrados:")
        for erro in erros:
            print(f"   - {erro}")
        return False, resultados
    else:
        print("\n✅ [OCR] Validação visual OK - Todos os campos conferem!")
        return True, resultados

# =================== GOOGLE SHEETS ===================
def buscar_item_teste():
    """Busca primeira linha disponível da planilha de teste"""
    print("\n📋 Conectando ao Google Sheets...")

    token_path = "token.json"
    creds_path = "CredenciaisOracle.json"

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build("sheets", "v4", credentials=creds)

    # Buscar dados
    res = service.spreadsheets().values().get(
        spreadsheetId=PLANILHA_TESTE_ID,
        range=f"{SHEET_NAME}!A1:AC"
    ).execute()

    valores = res.get("values", [])
    if not valores:
        print("❌ Nenhum dado encontrado na planilha")
        return None

    headers, dados = valores[0], valores[1:]

    # Buscar primeira linha com Status = CONCLUÍDO e Status Oracle vazio
    for i, row in enumerate(dados):
        if len(row) < len(headers):
            row += [''] * (len(headers) - len(row))

        linha_dict = dict(zip(headers, row))
        status = linha_dict.get("Status", "").strip().upper()
        status_oracle = linha_dict.get("Status Oracle", "").strip()

        if "CONCLUÍDO" in status and status_oracle == "":
            print(f"✅ Linha {i+2} encontrada para teste:")
            print(f"   Item: {linha_dict.get('Item', '')}")
            print(f"   Quantidade: {linha_dict.get('Quantidade', '')}")
            print(f"   Status: {status}")
            return linha_dict

    print("⚠️ Nenhuma linha disponível para teste (precisa ter Status=CONCLUÍDO e Status Oracle vazio)")
    return None

# =================== TESTE PRINCIPAL ===================
def main():
    print("="*70)
    print("   TESTE DE SIMULAÇÃO OCR - SEM CTRL+S")
    print("="*70)
    print()
    print("⚠️  IMPORTANTE: Este teste NÃO executará Ctrl+S")
    print("⚠️  Apenas simula o preenchimento e valida com OCR")
    print()

    # Buscar dados da planilha
    item_teste = buscar_item_teste()
    if not item_teste:
        print("\n❌ Não foi possível buscar dados da planilha")
        return

    # Extrair dados
    item = item_teste.get("Item", "").strip()
    quantidade = item_teste.get("Quantidade", "").strip()
    referencia = item_teste.get("Cód Referencia", "").strip()
    sub_o = item_teste.get("Sub.Origem", "").strip()
    end_o = item_teste.get("End. Origem", "").strip()
    sub_d = item_teste.get("Sub. Destino", "").strip()
    end_d = item_teste.get("End. Destino", "").strip()

    print("\n" + "="*70)
    print("   CENÁRIO 1: PREENCHIMENTO CORRETO (deveria passar no OCR)")
    print("="*70)
    print("\n⏳ Você tem 5 segundos para posicionar o Oracle na tela...")
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)

    print("\n🖱️ Iniciando preenchimento CORRETO dos campos...")

    # Preencher Item
    print(f"\n📝 Preenchendo Item: {item}")
    pyautogui.click(coords["item"])
    time.sleep(0.3)
    pyautogui.press("delete")
    time.sleep(0.2)
    pyautogui.write(item)
    time.sleep(0.5)

    # Preencher Referência
    print(f"📝 Preenchendo Referência: {referencia}")
    pyautogui.click(coords["Referencia"])
    time.sleep(0.3)
    pyautogui.write(referencia)
    time.sleep(0.5)

    # Preencher Sub.Origem
    print(f"📝 Preenchendo Sub.Origem: {sub_o}")
    pyautogui.click(coords["sub_origem"])
    time.sleep(0.3)
    pyautogui.write(sub_o)
    time.sleep(0.5)

    # Preencher End.Origem
    print(f"📝 Preenchendo End.Origem: {end_o}")
    pyautogui.click(coords["end_origem"])
    time.sleep(0.3)
    pyautogui.write(end_o)
    time.sleep(0.5)

    # Se não é COD, preencher destino
    if not str(referencia).strip().upper().startswith("COD"):
        print(f"📝 Preenchendo Sub.Destino: {sub_d}")
        pyautogui.click(coords["sub_destino"])
        time.sleep(0.3)
        pyautogui.write(sub_d)
        time.sleep(0.5)

        print(f"📝 Preenchendo End.Destino: {end_d}")
        pyautogui.click(coords["end_destino"])
        time.sleep(0.3)
        pyautogui.write(end_d)
        time.sleep(0.5)

    # Preencher Quantidade
    print(f"📝 Preenchendo Quantidade: {quantidade}")
    pyautogui.click(coords["quantidade"])
    time.sleep(0.3)
    pyautogui.write(quantidade)
    time.sleep(1)

    # Validar com OCR
    print("\n⏳ Aguardando 2 segundos para estabilização da tela...")
    time.sleep(2)

    ocr_ok_correto, resultados_correto = validar_campos_oracle_ocr(
        coords, item, quantidade, referencia,
        sub_o, end_o, sub_d, end_d
    )

    if ocr_ok_correto:
        print("\n✅ CENÁRIO 1: OCR APROVARIA - Ctrl+S seria executado (mas não executamos)")
    else:
        print("\n❌ CENÁRIO 1: OCR BLOQUEARIA - Ctrl+S seria abortado")

    # Aguardar antes do próximo cenário
    print("\n" + "="*70)
    print("   CENÁRIO 2: PREENCHIMENTO ERRADO (deveria FALHAR no OCR)")
    print("="*70)
    print("\n⏳ Aguardando 5 segundos antes do próximo cenário...")
    time.sleep(5)

    print("\n🖱️ Iniciando preenchimento ERRADO dos campos...")
    print("   (vou digitar valores propositalmente diferentes)")

    # Limpar e preencher com valores errados
    print(f"\n📝 Preenchendo Item ERRADO: 99999 (esperado: {item})")
    pyautogui.click(coords["item"])
    time.sleep(0.3)
    pyautogui.press("delete")
    time.sleep(0.2)
    pyautogui.write("99999")
    time.sleep(0.5)

    print(f"📝 Preenchendo Quantidade ERRADA: 9999 (esperado: {quantidade})")
    pyautogui.click(coords["quantidade"])
    time.sleep(0.3)
    pyautogui.press("delete")
    time.sleep(0.2)
    pyautogui.write("9999")
    time.sleep(1)

    # Validar com OCR (valores errados)
    print("\n⏳ Aguardando 2 segundos para estabilização da tela...")
    time.sleep(2)

    ocr_ok_errado, resultados_errado = validar_campos_oracle_ocr(
        coords, item, quantidade, referencia,
        sub_o, end_o, sub_d, end_d
    )

    if ocr_ok_errado:
        print("\n⚠️ CENÁRIO 2: OCR APROVARIA (ERRO! Deveria ter bloqueado)")
    else:
        print("\n✅ CENÁRIO 2: OCR BLOQUEARIA CORRETAMENTE - Ctrl+S seria abortado")

    # Relatório final
    print("\n" + "="*70)
    print("   RELATÓRIO FINAL DO TESTE")
    print("="*70)

    print("\n📊 CENÁRIO 1 - Preenchimento Correto:")
    print(f"   Resultado: {'✅ PASSOU' if ocr_ok_correto else '❌ FALHOU'}")
    print("   Campos validados:")
    for res in resultados_correto:
        simbolo = "✅" if res["sucesso"] else "❌"
        print(f"      {simbolo} {res['campo']}: esperado='{res['esperado']}', lido='{res['lido']}', confiança={res['confianca']*100:.1f}%")

    print("\n📊 CENÁRIO 2 - Preenchimento Errado:")
    print(f"   Resultado: {'❌ PASSOU (ERRO!)' if ocr_ok_errado else '✅ BLOQUEOU CORRETAMENTE'}")
    print("   Campos validados:")
    for res in resultados_errado:
        simbolo = "✅" if res["sucesso"] else "❌"
        print(f"      {simbolo} {res['campo']}: esperado='{res['esperado']}', lido='{res['lido']}', confiança={res['confianca']*100:.1f}%")

    print("\n" + "="*70)
    print("   LIMPANDO CAMPOS DO ORACLE")
    print("="*70)
    print("\n🧹 Apagando todos os campos preenchidos durante o teste...")

    # Limpar todos os campos
    campos_para_limpar = [
        ("Item", coords["item"]),
        ("Referência", coords["Referencia"]),
        ("Sub.Origem", coords["sub_origem"]),
        ("End.Origem", coords["end_origem"]),
        ("Sub.Destino", coords["sub_destino"]),
        ("End.Destino", coords["end_destino"]),
        ("Quantidade", coords["quantidade"]),
    ]

    for nome_campo, (x, y) in campos_para_limpar:
        try:
            print(f"   🧹 Limpando {nome_campo}...")
            pyautogui.click(x, y)
            time.sleep(0.2)
            # Selecionar tudo e deletar
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(0.1)
            pyautogui.press('delete')
            time.sleep(0.2)
        except Exception as e:
            print(f"      ⚠️ Erro ao limpar {nome_campo}: {e}")

    print("\n✅ Campos limpos com sucesso!")

    print("\n" + "="*70)
    print("   TESTE CONCLUÍDO")
    print("="*70)
    print("\n⚠️  Lembre-se: Nenhum Ctrl+S foi executado!")
    print("⚠️  Os dados NÃO foram salvos no Oracle")
    print("✅  Todos os campos foram limpos!")
    print("\n📁 Screenshots salvos para debug:")
    print("   - debug_ocr_*.png (capturas de cada campo)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
