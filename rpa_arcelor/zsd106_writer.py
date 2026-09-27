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
        # Paginado igual _buscar_pre_picking: o PostgREST corta em 1000 linhas
        # por padrão. Sem isso, um lote grande de itens existentes voltaria
        # truncado — os itens além do corte pareceriam "novos" (duplicata) e
        # os que ficaram fora da reconciliação escapariam do zera/exclui.
        desde = 0
        while True:
            resp_itens = (
                cliente.table("transporte_itens")
                .select("id, transporte_id, sku, separa_por_unidade, quantidade_pedido, unidades_pedido, deleted_at")
                .in_("transporte_id", ids)
                .range(desde, desde + 999)
                .execute()
            )
            linhas = resp_itens.data or []
            for item in linhas:
                itens_por_transporte.setdefault(item["transporte_id"], {})[
                    _identidade(item["sku"], bool(item["separa_por_unidade"]))
                ] = item
            if len(linhas) < 1000:
                break
            desde += 1000

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
    mesmos filtros, mesma chave.

    LIMITAÇÃO CONHECIDA (RLS): sob RLS, uma consulta SELECT que a policy nega
    volta HTTP 200 com `data: []` — exatamente igual a "não tem nada mesmo no
    pré-picking". Não tem como este código distinguir os dois casos a partir
    só da resposta vazia. Se a permissão de SELECT da conta de serviço em
    `movimentacao_armazenagem` for restringida no futuro, esta função passaria
    a devolver `{}` pra tudo silenciosamente — e TODO item que sumiu do
    arquivo seria tratado como "sem pré-picking" e apagado (`deleted_at`) em
    vez de zerado, violando exatamente a regra que este módulo existe pra
    garantir ("nunca esconder um problema de estoque já separado"). Isso não
    dá pra blindar só com código aqui: precisa de uma checagem de
    permissões/RLS contra staging (confirmar que a role da conta de serviço
    realmente tem SELECT nesta tabela) como passo de implantação, antes da
    primeira rodada real em produção."""
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


def _exigir_linha(resp, descricao: str):
    """Sob RLS, um INSERT/UPDATE que a policy nega volta HTTP 200 com `data`
    vazio — indistinguível, só pelo retorno, de um erro de rede que o
    supabase-py já levantaria como exceção. Uma operação que deveria afetar
    EXATAMENTE uma linha (por id) e voltou vazia não pode ser contada como
    sucesso silenciosamente: melhor parar tudo com um erro claro do que seguir
    incrementando o resumo como se a gravação em produção tivesse acontecido."""
    if not resp.data:
        raise RuntimeError(
            f"{descricao} não retornou nenhuma linha — pode ter sido negado por RLS "
            f"(a role da conta de serviço não tem permissão sobre este registro) e NADA foi gravado."
        )
    return resp.data


def gravar_zsd106(cliente, transportes: list, usuario_id, transportes_com_linha_invalida=None) -> dict:
    """`transportes_com_linha_invalida` (opcional): conjunto de
    `numero_transporte` que tiveram ao menos uma linha rejeitada por
    `parse_zsd106` nesta leitura (ver zsd106_parser). Pra esses, a leitura NÃO
    é tratada como completa/confiável o bastante pra apagar ou zerar item que
    "sumiu" — só os itens que de fato vieram no arquivo são inseridos/
    atualizados normalmente."""
    transportes_com_linha_invalida = transportes_com_linha_invalida or set()
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
            transporte_id = _exigir_linha(resp, f"insert em transportes (numero_transporte={t['numero_transporte']})")[0]["id"]
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
                item_id = _exigir_linha(
                    resp_item, f"insert em transporte_itens (transporte_id={transporte_id}, sku={item['sku']})"
                )[0]["id"]
                resumo["inseridos"] += 1
                _regravar_ordens(cliente, item_id, item["ordens"])
                continue

            item_id = atual["id"]
            mesmo_peso = pesos_iguais(atual["quantidade_pedido"], item["quantidade"])
            mesmas_unidades = pesos_iguais(atual.get("unidades_pedido") or 0, item["unidades"] or 0)
            estava_apagado = atual.get("deleted_at") is not None
            if mesmo_peso and mesmas_unidades and not estava_apagado:
                continue  # igual ao que já está gravado e não estava apagado: não mexe (nem na quebra por ordem)

            resp_update = (
                cliente.table("transporte_itens")
                .update(
                    {
                        "quantidade_pedido": item["quantidade"],
                        "unidades_pedido": item["unidades"],
                        "deleted_at": None,
                    }
                )
                .eq("id", item_id)
                .execute()
            )
            _exigir_linha(resp_update, f"update em transporte_itens id={item_id}")
            resumo["atualizados"] += 1
            _regravar_ordens(cliente, item_id, item["ordens"])

        if t["numero_transporte"] in transportes_com_linha_invalida:
            # Leitura teve linha inválida pra este transporte: não é seguro
            # tratar item que não veio em `vistos` como "sumiu de verdade" do
            # SAP (pode ter sido só a linha dele que falhou o parse). Os
            # inserts/updates dos itens que VIERAM certos já rodaram acima.
            continue

        for identidade, item_gravado in itens_existentes.items():
            if identidade in vistos:
                continue
            chave_pp = (
                f"{transporte_id}|{item_gravado['sku']}|"
                f"{'un' if item_gravado['separa_por_unidade'] else 'kg'}"
            )
            no_pre_picking = pre_picking.get(chave_pp, 0.0)
            if no_pre_picking > 0:
                resp_zero = (
                    cliente.table("transporte_itens")
                    .update(
                        {
                            "quantidade_pedido": 0,
                            "unidades_pedido": 0 if item_gravado["separa_por_unidade"] else None,
                            # Limpa um deleted_at de uma rodada anterior: o item
                            # voltou a ter material físico em pré-picking, não
                            # pode continuar marcado/escondido como apagado.
                            "deleted_at": None,
                        }
                    )
                    .eq("id", item_gravado["id"])
                    .execute()
                )
                _exigir_linha(resp_zero, f"update (zerar) em transporte_itens id={item_gravado['id']}")
                cliente.table("arc_item_ordem_venda").delete().eq(
                    "transporte_item_id", item_gravado["id"]
                ).execute()
                resumo["zerados"] += 1
            else:
                if item_gravado.get("deleted_at") is not None:
                    # Já apagado numa rodada anterior e continua sem
                    # pré-picking: não re-carimba deleted_at (perderia o
                    # horário original) nem conta de novo no resumo.
                    continue
                resp_excluir = (
                    cliente.table("transporte_itens")
                    .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
                    .eq("id", item_gravado["id"])
                    .execute()
                )
                _exigir_linha(resp_excluir, f"update (apagar) em transporte_itens id={item_gravado['id']}")
                cliente.table("arc_item_ordem_venda").delete().eq(
                    "transporte_item_id", item_gravado["id"]
                ).execute()
                resumo["excluidos"] += 1

    return resumo
