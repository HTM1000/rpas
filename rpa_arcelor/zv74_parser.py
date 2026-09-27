# -*- coding: utf-8 -*-
"""Parser do ZV74 (observações de embarque + condição de pagamento) — espelha
wmsarcelormital/src/lib/observacoesEmbarqueParser.ts."""
from normalizacao import remover_zeros_esquerda, normalizar_cabecalho

COL_FORNECIMENTO = "Número do fornecimento"
COL_TEXTO = "Texto Embarque"
COL_ORDEM_VENDA = "Ordem Vendas"
COL_COND_PAGTO = "Desc Cond Pagto"


def _indice(cabecalho: list, titulo: str):
    alvo = normalizar_cabecalho(titulo)
    return cabecalho.index(alvo) if alvo in cabecalho else None


def parse_zv74(linhas: list) -> dict:
    """`linhas[0]` é o cabeçalho, `linhas[1:]` os dados — mesmo formato que
    `ws.iter_rows(values_only=True)` do openpyxl devolve (como lista)."""
    if not linhas:
        return {"observacoes": [], "condicoes_pagamento": [], "linhas_sem_texto": 0, "linhas_sem_fornecimento": 0}

    cabecalho = [normalizar_cabecalho(str(v) if v is not None else "") for v in linhas[0]]
    idx_fornecimento = _indice(cabecalho, COL_FORNECIMENTO)
    idx_textos = [i for i, c in enumerate(cabecalho) if c == normalizar_cabecalho(COL_TEXTO)]

    if idx_fornecimento is None or not idx_textos:
        raise ValueError(f"Planilha não reconhecida: não encontrei as colunas esperadas ({COL_FORNECIMENTO}, {COL_TEXTO}).")

    idx_ordem_venda = _indice(cabecalho, COL_ORDEM_VENDA)
    idx_cond_pagto = _indice(cabecalho, COL_COND_PAGTO)

    linhas_sem_texto = 0
    linhas_sem_fornecimento = 0
    por_fornecimento = {}
    por_ordem_venda = {}

    for row in linhas[1:]:
        if row is None:
            continue

        def celula(idx):
            if idx is None or idx >= len(row) or row[idx] is None:
                return ""
            return str(row[idx]).strip()

        if idx_ordem_venda is not None and idx_cond_pagto is not None:
            ordem_venda = remover_zeros_esquerda(celula(idx_ordem_venda))
            descricao = celula(idx_cond_pagto)
            if ordem_venda and descricao and ordem_venda not in por_ordem_venda:
                por_ordem_venda[ordem_venda] = descricao

        texto = next((t for t in (celula(i) for i in idx_textos) if t != ""), "")
        fornecimento = remover_zeros_esquerda(celula(idx_fornecimento))

        if not texto:
            linhas_sem_texto += 1
            continue
        if not fornecimento:
            linhas_sem_fornecimento += 1
            continue
        if fornecimento not in por_fornecimento:
            por_fornecimento[fornecimento] = texto

    return {
        "observacoes": [{"fornecimento": f, "texto": t} for f, t in por_fornecimento.items()],
        "condicoes_pagamento": [{"ordem_venda": o, "descricao": d} for o, d in por_ordem_venda.items()],
        "linhas_sem_texto": linhas_sem_texto,
        "linhas_sem_fornecimento": linhas_sem_fornecimento,
    }
