#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste das melhorias de correção OCR

Testa os cenários reportados pelo usuário:
1. "E2o294" deve virar "E2029A" (o→0 no meio + 4→A no final)
2. "£20298" deve virar "E2029B" (£→E no início + 8→B no final)
"""

import re

def corrigir_confusao_ocr(texto):
    """
    Corrige caracteres comumente confundidos pelo OCR.

    Confusões comuns:
    - A ↔ 4
    - B ↔ 8
    - O ↔ 0 (letra o ↔ zero)
    - I ↔ 1
    - S ↔ 5
    - Z ↔ 2

    MELHORIAS IMPLEMENTADAS:
    1. Correção de símbolos especiais: £→E, €→E (ex: "£20298" → "E20298")
    2. Correção de o→0 em qualquer posição (ex: "E2o294" → "E20294")
    3. Validação contextual para padrões letra+dígitos+letra
    4. Correção do último caractere (ex: "E20294" → "E2029A", "E20298" → "E2029B")

    Args:
        texto: Texto lido pelo OCR

    Returns:
        str: Texto com correções aplicadas
    """
    if not texto:
        return texto

    texto_original = texto
    texto_corrigido = texto.upper().strip()

    # ═══════════════════════════════════════════════════════════════
    # PASSO 0: Corrigir símbolos especiais confundidos (£ → E)
    # ═══════════════════════════════════════════════════════════════
    # OCR frequentemente confunde E com £ no início de códigos
    if texto_corrigido.startswith('£'):
        texto_corrigido = 'E' + texto_corrigido[1:]
        # print(f"[OCR SIMBOLO] 'libra' -> 'E' (inicio de codigo)")

    # Corrigir outros símbolos comuns
    texto_corrigido = texto_corrigido.replace('€', 'E')  # Euro → E
    texto_corrigido = texto_corrigido.replace('£', 'E')  # Libra → E (qualquer posição)

    # ═══════════════════════════════════════════════════════════════
    # PASSO 1: Corrigir confusões letra↔número em QUALQUER POSIÇÃO
    # ═══════════════════════════════════════════════════════════════
    # Detectar padrão: Começa com LETRA (contexto alfanumérico)
    if re.match(r'^[A-Z]', texto_corrigido):
        # Mapa de correções bidirecionais
        correcoes_posicao = {
            'o': '0',  # letra o minúscula → zero (CRÍTICO para "E2o294" → "E20294")
            'O': '0',  # letra O maiúscula → zero
            'l': '1',  # letra l minúscula → um
            'I': '1',  # letra I maiúscula → um (em contexto numérico)
            's': '5',  # letra s minúscula → cinco
            'S': '5',  # letra S maiúscula → cinco
            'z': '2',  # letra z minúscula → dois
            'Z': '2',  # letra Z maiúscula → dois
        }

        # Aplicar correções em todo o texto (exceto primeiro caractere que é letra)
        resultado = texto_corrigido[0]  # Preserva primeira letra
        for i, char in enumerate(texto_corrigido[1:], start=1):
            # Se encontrar letra minúscula em contexto numérico, corrigir
            if char in correcoes_posicao:
                # Verificar se há dígitos ao redor (contexto numérico)
                tem_digito_antes = i > 1 and texto_corrigido[i-1].isdigit()
                tem_digito_depois = i < len(texto_corrigido)-1 and texto_corrigido[i+1].isdigit()

                if tem_digito_antes or tem_digito_depois:
                    resultado += correcoes_posicao[char]
                else:
                    resultado += char
            else:
                resultado += char

        texto_corrigido = resultado

    # ═══════════════════════════════════════════════════════════════
    # PASSO 2: Correção do ÚLTIMO CARACTERE (letra confundida com número)
    # ═══════════════════════════════════════════════════════════════
    # Padrão: Letra + dígitos + NÚMERO_FINAL que pode ser letra
    # Ex: E20294 → E2029A (4→A), E20298 → E2029B (8→B)
    match = re.match(r'^([A-Z]+\d+)([0-9])$', texto_corrigido)

    if match:
        prefixo = match.group(1)  # Ex: "E2029"
        ultimo = match.group(2)    # Ex: "4" ou "8"

        # Mapa de confusão comum no final de códigos
        mapa_final = {
            '4': 'A',
            '8': 'B',
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '2': 'Z'
        }

        if ultimo in mapa_final:
            texto_corrigido = prefixo + mapa_final[ultimo]

    # Log apenas se houve correção
    if texto_corrigido != texto_original.upper().strip():
        return texto_corrigido

    return texto


def teste_correcoes():
    """Testa todos os cenários de correção OCR"""

    print("=" * 70)
    print("TESTE DE CORREÇÕES OCR")
    print("=" * 70)

    casos_teste = [
        # (entrada_ocr, esperado, descrição)
        ("E2o294", "E2029A", "o->0 no meio + 4->A no final"),
        ("£20298", "E2029B", "libra->E no inicio + 8->B no final"),
        ("E20294", "E2029A", "4->A no final (basico)"),
        ("E20298", "E2029B", "8->B no final (basico)"),
        ("E2029B", "E2029B", "Ja correto (nao deve alterar)"),
        ("E2029A", "E2029A", "Ja correto (nao deve alterar)"),
        ("€20294", "E2029A", "euro->E no inicio + 4->A no final"),
        ("E2o29B", "E2029B", "o->0 no meio, ja tem B no final"),
        ("E202OB", "E2020B", "O maiusculo->0 no meio"),
        ("Elol94", "E1014", "l->1 multiplos + 4->A no final"),
    ]

    passou = 0
    falhou = 0

    for i, (entrada, esperado, descricao) in enumerate(casos_teste, 1):
        resultado = corrigir_confusao_ocr(entrada)

        status = "[OK] PASSOU" if resultado == esperado else "[FALHOU]"
        if resultado == esperado:
            passou += 1
        else:
            falhou += 1

        print(f"\nTeste {i}: {descricao}")
        print(f"  Entrada: '{entrada}'")
        print(f"  Esperado: '{esperado}'")
        print(f"  Obtido: '{resultado}'")
        print(f"  {status}")

    print("\n" + "=" * 70)
    print(f"RESULTADOS: {passou} passou, {falhou} falhou de {len(casos_teste)} testes")
    print("=" * 70)

    return falhou == 0


if __name__ == "__main__":
    sucesso = teste_correcoes()
    exit(0 if sucesso else 1)
