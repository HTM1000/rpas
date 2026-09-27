# -*- coding: utf-8 -*-
"""Grava a leitura do ZSD106 no Supabase: reconciliação item a item, espelhando
wmsarcelormital/src/components/ImportarTransportesButton.tsx (caminho da
expedição) — mesmas tabelas, mesma regra de status elegível, e `deleted_at` no
lugar do delete/zera de hoje quando o item some do arquivo."""
from datetime import datetime, timezone
from normalizacao import pesos_iguais

STATUS_ELEGIVEL = {"agendado", "em_andamento"}


def _identidade(sku: str, por_unidade: bool) -> str:
    return f"{sku}|{'un' if por_unidade else 'kg'}"


def _buscar_existentes(cliente, numeros_transporte):
    if not numeros_transporte:
        return {}
    resp = (
        cliente.table("transportes")
        .select("id, numero_transporte, status")
        .in_("numero_transporte", numeros_transporte)
        .eq("tipo", "expedicao")
        .execute()
    )
    transportes = resp.data or []
    ids = [t["id"] for t in transportes]

    itens_por_transporte = {}
    if ids:
        resp_itens = (
            cliente.table("transporte_itens")
            .select("id, transporte_id, sku, separa_por_unidade, quantidade_pedido, unidades_pedido")
            .in_("transporte_id", ids)
            .execute()
        )
        for item in resp_itens.data or []:
            itens_por_transporte.setdefault(item["transporte_id"], {})[
                _identidade(item["sku"], bool(item["separa_por_unidade"]))
            ] = item

    resultado = {}
    for t in transportes:
        resultado[t["numero_transporte"]] = {
            "id": t["id"],
            "status": t["status"],
            "itens": itens_por_transporte.get(t["id"], {}),
        }
    return resultado


def _buscar_pre_picking(cliente, transporte_ids):
    """Peso que cada linha (transporte_id|sku|kg-ou-un) ainda tem FISICAMENTE
    no pré-picking. Espelha buscarMaterialNoPrePicking
    (wmsarcelormital/src/features/arcelor/itemRetirado.ts) — mesma tabela,
    mesmos filtros, mesma chave."""
    resultado = {}
    if not transporte_ids:
        return resultado
    for inicio in range(0, len(transporte_ids), 200):
        lote = transporte_ids[inicio : inicio + 200]
        desde = 0
        while True:
            resp = (
                cliente.table("movimentacao_armazenagem")
                .select("sku, transporte_id, quantidade, unidades")
                .eq("tipo_transporte", "Picking")
                .is_("devolver_desde", None)
                .is_("devolvido_em", None)
                .in_("transporte_id", lote)
                .range(desde, desde + 999)
                .execute()
            )
            linhas = resp.data or []
            for linha in linhas:
                if not linha.get("transporte_id"):
                    continue
                por_unidade = linha.get("unidades") is not None
                chave = f"{linha['transporte_id']}|{linha['sku']}|{'un' if por_unidade else 'kg'}"
                resultado[chave] = resultado.get(chave, 0.0) + float(linha.get("quantidade") or 0)
            if len(linhas) < 1000:
                break
            desde += 1000
    return resultado


def _regravar_ordens(cliente, transporte_item_id, ordens):
    """Reescreve a quebra por fornecimento/ordem de venda: apaga as antigas e
    insere as novas — uma reimportação troca o roteiro inteiro."""
    cliente.table("arc_item_ordem_venda").delete().eq("transporte_item_id", transporte_item_id).execute()
    if not ordens:
        return
    linhas = [
        {
            "transporte_item_id": transporte_item_id,
            "fornecimento": o["fornecimento"],
            "ordem_venda": o["ordem_venda"],
            "quantidade_kg": o["quantidade"],
            "unidades": o["unidades"],
            "ordem": idx + 1,
        }
        for idx, o in enumerate(ordens)
    ]
    cliente.table("arc_item_ordem_venda").insert(linhas).execute()


def gravar_zsd106(cliente, transportes: list, usuario_id) -> dict:
    numeros = [t["numero_transporte"] for t in transportes]
    existentes = _buscar_existentes(cliente, numeros)

    ids_elegiveis = [
        existentes[t["numero_transporte"]]["id"]
        for t in transportes
        if t["numero_transporte"] in existentes
        and existentes[t["numero_transporte"]]["status"] in STATUS_ELEGIVEL
    ]
    pre_picking = _buscar_pre_picking(cliente, ids_elegiveis)

    resumo = {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0}

    for t in transportes:
        existente = existentes.get(t["numero_transporte"])
        if existente and existente["status"] not in STATUS_ELEGIVEL:
            continue  # transporte encerrado: o ZSD106 não reabre

        if existente:
            transporte_id = existente["id"]
        else:
            resp = (
                cliente.table("transportes")
                .insert(
                    {
                        "numero_transporte": t["numero_transporte"],
                        "tipo": "expedicao",
                        "status": "agendado",
                        "hora_agenda": None,
                        "placa": None,
                        "origem": None,
                        "transportadora": None,
                        "notas_fiscais": None,
                        "fornecimentos": t["fornecimentos"] or None,
                        "usuario_id": usuario_id,
                        "input_manual": False,
                        "status_consulta_sap": True,
                    }
                )
                .execute()
            )
            transporte_id = resp.data[0]["id"]
            existente = {"id": transporte_id, "status": "agendado", "itens": {}}

        itens_existentes = dict(existente["itens"])
        vistos = set()

        for item in t["itens"]:
            identidade = _identidade(item["sku"], item["por_unidade"])
            vistos.add(identidade)
            atual = itens_existentes.get(identidade)

            if atual is None:
                resp_item = (
                    cliente.table("transporte_itens")
                    .insert(
                        {
                            "transporte_id": transporte_id,
                            "sku": item["sku"],
                            "quantidade_pedido": item["quantidade"],
                            "separa_por_unidade": item["por_unidade"],
                            "unidades_pedido": item["unidades"],
                        }
                    )
                    .execute()
                )
                item_id = resp_item.data[0]["id"]
                resumo["inseridos"] += 1
                _regravar_ordens(cliente, item_id, item["ordens"])
                continue

            item_id = atual["id"]
            mesmo_peso = pesos_iguais(atual["quantidade_pedido"], item["quantidade"])
            mesmas_unidades = (atual.get("unidades_pedido") or 0) == (item["unidades"] or 0)
            if mesmo_peso and mesmas_unidades:
                continue  # igual ao que já está gravado: não mexe (nem na quebra por ordem)

            cliente.table("transporte_itens").update(
                {"quantidade_pedido": item["quantidade"], "unidades_pedido": item["unidades"]}
            ).eq("id", item_id).execute()
            resumo["atualizados"] += 1
            _regravar_ordens(cliente, item_id, item["ordens"])

        for identidade, item_gravado in itens_existentes.items():
            if identidade in vistos:
                continue
            chave_pp = (
                f"{transporte_id}|{item_gravado['sku']}|"
                f"{'un' if item_gravado['separa_por_unidade'] else 'kg'}"
            )
            no_pre_picking = pre_picking.get(chave_pp, 0.0)
            if no_pre_picking > 0:
                cliente.table("transporte_itens").update(
                    {
                        "quantidade_pedido": 0,
                        "unidades_pedido": 0 if item_gravado["separa_por_unidade"] else None,
                    }
                ).eq("id", item_gravado["id"]).execute()
                resumo["zerados"] += 1
            else:
                cliente.table("transporte_itens").update(
                    {"deleted_at": datetime.now(timezone.utc).isoformat()}
                ).eq("id", item_gravado["id"]).execute()
                resumo["excluidos"] += 1

    return resumo
