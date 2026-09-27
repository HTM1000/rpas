# -*- coding: utf-8 -*-
"""Duplo de teste do cliente supabase-py: registra as chamadas encadeadas
(`.table().select()/.insert()/.update()/.upsert()/.delete().eq()/.in_()/.is_()`)
e devolve dados combinados de antemão — sem rede, pra testar a reconciliação
de verdade."""


class _RespostaFalsa:
    def __init__(self, data):
        self.data = data


class _ConstrutorFalso:
    def __init__(self, tabela, operacao, payload=None):
        self.tabela = tabela
        self.operacao = operacao
        self.payload = payload
        self.filtros = []

    def eq(self, coluna, valor):
        self.filtros.append(("eq", coluna, valor))
        return self

    def in_(self, coluna, valores):
        self.filtros.append(("in_", coluna, list(valores)))
        return self

    def is_(self, coluna, valor):
        self.filtros.append(("is_", coluna, valor))
        return self

    def range(self, desde, ate):
        self.filtros.append(("range", desde, ate))
        return self

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        chamada = {
            "tabela": self.tabela.nome,
            "operacao": self.operacao,
            "payload": self.payload,
            "filtros": list(self.filtros),
        }
        self.tabela.cliente.chamadas.append(chamada)
        dados = self.tabela.cliente.respostas.get(self.tabela.nome, {}).get(self.operacao, [])
        if callable(dados):
            dados = dados(chamada)
        return _RespostaFalsa(dados)


class _TabelaFalsa:
    def __init__(self, cliente, nome):
        self.cliente = cliente
        self.nome = nome

    def select(self, *_args, **_kwargs):
        return _ConstrutorFalso(self, "select")

    def insert(self, payload):
        return _ConstrutorFalso(self, "insert", payload)

    def update(self, payload):
        return _ConstrutorFalso(self, "update", payload)

    def upsert(self, payload, on_conflict=None):
        return _ConstrutorFalso(self, "upsert", {"linhas": payload, "on_conflict": on_conflict})

    def delete(self):
        return _ConstrutorFalso(self, "delete")


class FakeSupabaseClient:
    """`respostas` é `{tabela: {operacao: linhas_ou_funcao(chamada)->linhas}}` —
    o que `.execute().data` deve devolver para cada tabela/operação."""

    def __init__(self, respostas=None):
        self.respostas = respostas or {}
        self.chamadas = []

    def table(self, nome):
        return _TabelaFalsa(self, nome)
