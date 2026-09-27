# -*- coding: utf-8 -*-
import unittest
from supabase_fake import FakeSupabaseClient
from zv74_writer import gravar_zv74

RESULTADO = {
    "observacoes": [{"fornecimento": "846252364", "texto": "ENVIAR 300 BARRAS"}],
    "condicoes_pagamento": [{"ordem_venda": "201308660", "descricao": "A Prazo"}],
    "linhas_sem_texto": 0,
    "linhas_sem_fornecimento": 0,
}


class TestGravarZv74(unittest.TestCase):
    def test_upsert_observacoes_e_condicoes(self):
        cliente = FakeSupabaseClient()
        resumo = gravar_zv74(cliente, RESULTADO, usuario_id="U1")

        self.assertEqual(resumo, {"observacoes": 1, "condicoes_pagamento": 1})
        obs = [c for c in cliente.chamadas if c["tabela"] == "arc_observacao_embarque"]
        cond = [c for c in cliente.chamadas if c["tabela"] == "arc_condicao_pagamento_ordem"]
        self.assertEqual(obs[0]["operacao"], "upsert")
        self.assertEqual(obs[0]["payload"]["on_conflict"], "fornecimento")
        self.assertEqual(obs[0]["payload"]["linhas"][0]["fornecimento"], "846252364")
        self.assertEqual(cond[0]["payload"]["on_conflict"], "ordem_venda")

    def test_nao_grava_nada_quando_vazio(self):
        cliente = FakeSupabaseClient()
        resumo = gravar_zv74(
            cliente,
            {"observacoes": [], "condicoes_pagamento": [], "linhas_sem_texto": 0, "linhas_sem_fornecimento": 0},
            usuario_id="U1",
        )
        self.assertEqual(resumo, {"observacoes": 0, "condicoes_pagamento": 0})
        self.assertEqual(cliente.chamadas, [])


if __name__ == "__main__":
    unittest.main()
