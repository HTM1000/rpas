# -*- coding: utf-8 -*-
"""Grava observações de embarque e condição de pagamento em
arc_observacao_embarque / arc_condicao_pagamento_ordem — upsert, espelhando
observacoesEmbarqueParser.ts + o uso que ImportarTransportesButton.tsx faz
dele."""
from datetime import datetime, timezone


def gravar_zv74(cliente, resultado: dict, usuario_id) -> dict:
    agora = datetime.now(timezone.utc).isoformat()
    resumo = {"observacoes": 0, "condicoes_pagamento": 0}

    if resultado["observacoes"]:
        linhas = [
            {"fornecimento": o["fornecimento"], "texto": o["texto"], "atualizado_em": agora, "atualizado_por": usuario_id}
            for o in resultado["observacoes"]
        ]
        for inicio in range(0, len(linhas), 500):
            cliente.table("arc_observacao_embarque").upsert(linhas[inicio : inicio + 500], on_conflict="fornecimento").execute()
        resumo["observacoes"] = len(linhas)

    if resultado["condicoes_pagamento"]:
        linhas = [
            {"ordem_venda": c["ordem_venda"], "descricao": c["descricao"], "atualizado_em": agora, "atualizado_por": usuario_id}
            for c in resultado["condicoes_pagamento"]
        ]
        for inicio in range(0, len(linhas), 500):
            cliente.table("arc_condicao_pagamento_ordem").upsert(linhas[inicio : inicio + 500], on_conflict="ordem_venda").execute()
        resumo["condicoes_pagamento"] = len(linhas)

    return resumo
