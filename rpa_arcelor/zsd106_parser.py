# -*- coding: utf-8 -*-
"""Parser do ZSD106 (export do SAP): agrupa por transporte e por item (sku +
forma de separar), somando peso/unidade das linhas que se repetem por
fornecimento. Espelha wmsarcelormital/src/lib/agendaExpedicaoParser.ts —
com UMA diferença deliberada: aqui `Fornecimento` e `Doc. Modelo` (ordem de
venda) TAMBÉM perdem o zero à esquerda, pra casar com VT12/ZV74 (o front hoje
não tira desses dois campos nesse parser específico — inconsistência
preexistente que este robô não repete)."""
from normalizacao import (
    remover_zeros_esquerda,
    mapear_colunas,
    mapear_coluna_opcional,
    arredondar_peso,
    parse_numero_zsd106,
)

COLUNAS_OBRIGATORIAS = ["N° Transporte", "Material", "Quantidade", "Qtde"]


def _tentar_parse(texto: str):
    if not texto:
        return None
    try:
        return parse_numero_zsd106(texto)
    except ValueError:
        return None


def parse_zsd106(linhas: list[dict], colunas: list[str]) -> tuple[list[dict], list[str]]:
    """`linhas` = uma lista de dicts (uma por linha do export, valores como
    string — igual `df.to_dict('records')` de `ler_planilha` devolve).
    Retorna (transportes, linhas_invalidas)."""
    mapa = mapear_colunas(colunas, COLUNAS_OBRIGATORIAS)
    col_fornecimento = mapear_coluna_opcional(colunas, "Fornecimento")
    col_ordem_venda = mapear_coluna_opcional(colunas, "Doc. Modelo") or mapear_coluna_opcional(
        colunas, "Doc Modelo"
    )

    ordem_transportes: list[str] = []
    grupos: dict = {}
    linhas_invalidas: list[str] = []

    for i, linha in enumerate(linhas):
        numero_transporte = remover_zeros_esquerda(str(linha.get(mapa["N° Transporte"], "")).strip())
        if not numero_transporte:
            continue  # rodapé/sobra da planilha

        sku = remover_zeros_esquerda(str(linha.get(mapa["Material"], "")).strip().upper())
        fornecimento = (
            remover_zeros_esquerda(str(linha.get(col_fornecimento, "")).strip()) if col_fornecimento else ""
        )
        ordem_venda = (
            remover_zeros_esquerda(str(linha.get(col_ordem_venda, "")).strip()) if col_ordem_venda else ""
        )

        if not sku and not fornecimento:
            continue  # linha de total do arquivo

        texto_unidade = str(linha.get(mapa["Quantidade"], "")).strip()
        texto_peso = str(linha.get(mapa["Qtde"], "")).strip()

        motivos = []
        if not sku:
            motivos.append("Material vazio")

        unidade = _tentar_parse(texto_unidade)
        if unidade is None or unidade <= 0:
            motivos.append(f'Quantidade inválida ("{texto_unidade}")')

        peso = _tentar_parse(texto_peso)
        if peso is None or peso <= 0:
            motivos.append(f'Qtde inválida ("{texto_peso}")')

        if motivos:
            linhas_invalidas.append(f"Transporte {numero_transporte} (linha {i + 1}): " + ", ".join(motivos))
            continue

        if numero_transporte not in grupos:
            grupos[numero_transporte] = {"itens": {}, "linhas_arquivo": 0, "fornecimentos": []}
            ordem_transportes.append(numero_transporte)

        grupo = grupos[numero_transporte]
        grupo["linhas_arquivo"] += 1

        por_unidade = unidade != peso
        chave = f"{sku}|{'un' if por_unidade else 'kg'}"
        item = grupo["itens"].setdefault(
            chave,
            {"sku": sku, "quantidade": 0.0, "por_unidade": por_unidade, "unidades": 0.0 if por_unidade else None, "ordens": {}},
        )
        item["quantidade"] += peso
        if por_unidade:
            item["unidades"] = (item["unidades"] or 0.0) + unidade

        if por_unidade or fornecimento or ordem_venda:
            chave_ordem = f"{fornecimento}|{ordem_venda}"
            ordem_item = item["ordens"].setdefault(
                chave_ordem,
                {"fornecimento": fornecimento, "ordem_venda": ordem_venda, "quantidade": 0.0, "unidades": 0.0 if por_unidade else None},
            )
            ordem_item["quantidade"] += peso
            if por_unidade:
                ordem_item["unidades"] = (ordem_item["unidades"] or 0.0) + unidade

        if fornecimento and fornecimento not in grupo["fornecimentos"]:
            grupo["fornecimentos"].append(fornecimento)

    transportes = []
    for numero_transporte in ordem_transportes:
        grupo = grupos[numero_transporte]
        itens = []
        for item in grupo["itens"].values():
            itens.append(
                {
                    "sku": item["sku"],
                    "quantidade": arredondar_peso(item["quantidade"]),
                    "por_unidade": item["por_unidade"],
                    "unidades": arredondar_peso(item["unidades"]) if item["unidades"] is not None else None,
                    "ordens": [
                        {
                            "fornecimento": o["fornecimento"],
                            "ordem_venda": o["ordem_venda"],
                            "quantidade": arredondar_peso(o["quantidade"]),
                            "unidades": arredondar_peso(o["unidades"]) if o["unidades"] is not None else None,
                        }
                        for o in item["ordens"].values()
                    ],
                }
            )
        transportes.append(
            {
                "numero_transporte": numero_transporte,
                "itens": itens,
                "linhas_arquivo": grupo["linhas_arquivo"],
                "fornecimentos": grupo["fornecimentos"],
            }
        )

    return transportes, linhas_invalidas
