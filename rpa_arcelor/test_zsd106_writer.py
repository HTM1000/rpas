import unittest
from supabase_fake import FakeSupabaseClient
from zsd106_writer import gravar_zsd106

TRANSPORTE_NOVO = {
    "numero_transporte": "5100130964",
    "linhas_arquivo": 1,
    "fornecimentos": ["861886474"],
    "itens": [
        {"sku": "128046", "quantidade": 10.0, "por_unidade": False, "unidades": None, "ordens": [
            {"fornecimento": "861886474", "ordem_venda": "", "quantidade": 10.0, "unidades": None}
        ]},
    ],
}


class TestGravarZsd106(unittest.TestCase):
    def test_transporte_novo_insere_transporte_e_item(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [], "insert": [{"id": "T1"}]},
                "transporte_itens": {"select": [], "insert": [{"id": "I1"}]},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 1, "atualizados": 0, "excluidos": 0, "zerados": 0})
        insercoes_transporte = [c for c in cliente.chamadas if c["tabela"] == "transportes" and c["operacao"] == "insert"]
        self.assertEqual(len(insercoes_transporte), 1)
        payload = insercoes_transporte[0]["payload"]
        self.assertEqual(payload["numero_transporte"], "5100130964")
        self.assertEqual(payload["tipo"], "expedicao")
        self.assertEqual(payload["status"], "agendado")
        self.assertIsNone(payload["hora_agenda"])
        self.assertFalse(payload["input_manual"])

    def test_item_igual_nao_atualiza(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes_item, [])
        # Item igual não mexe nem na quebra por ordem (evita delete+insert à toa).
        mexeu_em_ordens = [c for c in cliente.chamadas if c["tabela"] == "arc_item_ordem_venda"]
        self.assertEqual(mexeu_em_ordens, [])

    def test_item_diferente_atualiza(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 5.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo["atualizados"], 1)
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes_item[0]["payload"]["quantidade_pedido"], 10.0)

    def test_item_sumido_sem_pre_picking_marca_deleted_at(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["excluidos"], 1)
        self.assertEqual(resumo["zerados"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertIn("deleted_at", atualizacoes[0]["payload"])

    def test_item_sumido_com_pre_picking_zera_sem_deleted_at(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {
                    "select": [{"sku": "128046", "transporte_id": "T1", "quantidade": 3.0, "unidades": None}]
                },
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["zerados"], 1)
        self.assertEqual(resumo["excluidos"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        payload = atualizacoes[0]["payload"]
        self.assertEqual(payload["quantidade_pedido"], 0)
        self.assertNotIn("deleted_at", payload)

    def test_transporte_finalizado_nao_e_mexido(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "finalizado"}]},
                "transporte_itens": {"select": []},
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        mexeu = [c for c in cliente.chamadas if c["tabela"] in ("transportes", "transporte_itens") and c["operacao"] in ("insert", "update")]
        self.assertEqual(mexeu, [])


if __name__ == "__main__":
    unittest.main()
