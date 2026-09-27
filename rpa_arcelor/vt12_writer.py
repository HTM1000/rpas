# -*- coding: utf-8 -*-
"""Grava a sequência de carregamento do VT12 em arc_transporte_fornecimento —
delete-then-insert por transporte, espelhando sequenciaCarregamentoParser.ts +
o uso que ImportarTransportesButton.tsx faz dele."""


def gravar_vt12(cliente, transportes: list) -> dict:
    resumo = {"transportes_gravados": 0, "transportes_sem_cadastro": 0}
    numeros = [t["numero_transporte"] for t in transportes]
    if not numeros:
        return resumo

    resp = cliente.table("transportes").select("id, numero_transporte").in_("numero_transporte", numeros).execute()
    id_por_numero = {t["numero_transporte"]: t["id"] for t in (resp.data or [])}

    for t in transportes:
        transporte_id = id_por_numero.get(t["numero_transporte"])
        if not transporte_id:
            resumo["transportes_sem_cadastro"] += 1
            continue

        cliente.table("arc_transporte_fornecimento").delete().eq("transporte_id", transporte_id).execute()
        if t["fornecimentos"]:
            linhas = [
                {
                    "transporte_id": transporte_id,
                    "fornecimento": f["fornecimento"],
                    "ordem_carregamento": f["ordem_carregamento"],
                    "cliente": f["cliente"],
                    "destino": f["destino"],
                    "uf": f["uf"],
                    "peso_kg": f["peso_kg"],
                }
                for f in t["fornecimentos"]
            ]
            cliente.table("arc_transporte_fornecimento").insert(linhas).execute()
        resumo["transportes_gravados"] += 1

    return resumo
