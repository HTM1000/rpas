import unittest
from supabase_fake import FakeSupabaseClient
from zsd106_writer import gravar_zsd106, _buscar_existentes

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
                    ],
                    "update": [{"id": "I1"}],
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
                         "quantidade_pedido": 10.0, "unidades_pedido": None, "deleted_at": None}
                    ],
                    "update": [{"id": "I1"}],
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["excluidos"], 1)
        self.assertEqual(resumo["zerados"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertIn("deleted_at", atualizacoes[0]["payload"])
        # Item excluído não pode deixar rastro de ordem de venda ativo.
        ordens_apagadas = [c for c in cliente.chamadas if c["tabela"] == "arc_item_ordem_venda" and c["operacao"] == "delete"]
        self.assertEqual(len(ordens_apagadas), 1)
        self.assertIn(("eq", "transporte_item_id", "I1"), ordens_apagadas[0]["filtros"])

    def test_item_sumido_com_pre_picking_zera_sem_deleted_at(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None, "deleted_at": None}
                    ],
                    "update": [{"id": "I1"}],
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
        # Fix 5a: zerar TAMBÉM limpa um deleted_at de rodada anterior (o item
        # voltou a ter material físico separado, não pode ficar escondido).
        self.assertIn("deleted_at", payload)
        self.assertIsNone(payload["deleted_at"])
        # Item zerado também não pode deixar rastro de ordem de venda ativo.
        ordens_apagadas = [c for c in cliente.chamadas if c["tabela"] == "arc_item_ordem_venda" and c["operacao"] == "delete"]
        self.assertEqual(len(ordens_apagadas), 1)
        self.assertIn(("eq", "transporte_item_id", "I1"), ordens_apagadas[0]["filtros"])

    def test_item_zerado_com_deleted_at_previo_e_reativado(self):
        # Estava soft-deleted numa rodada anterior; agora tem pré-picking de
        # novo (ex.: reapareceu no depósito) — precisa sair do estado apagado.
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 0.0, "unidades_pedido": None,
                         "deleted_at": "2026-01-01T00:00:00+00:00"}
                    ],
                    "update": [{"id": "I1"}],
                },
                "movimentacao_armazenagem": {
                    "select": [{"sku": "128046", "transporte_id": "T1", "quantidade": 3.0, "unidades": None}]
                },
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["zerados"], 1)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertIsNone(atualizacoes[0]["payload"]["deleted_at"])

    def test_item_ja_apagado_sem_pre_picking_nao_e_re_carimbado(self):
        # Fix 5b: item já com deleted_at setado e continua sem pré-picking —
        # não deve gerar UPDATE nem ser contado de novo em "excluidos".
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 0.0, "unidades_pedido": None,
                         "deleted_at": "2026-01-01T00:00:00+00:00"}
                    ],
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["excluidos"], 0)
        self.assertEqual(resumo["zerados"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes, [])
        ordens_apagadas = [c for c in cliente.chamadas if c["tabela"] == "arc_item_ordem_venda"]
        self.assertEqual(ordens_apagadas, [])

    def test_item_reaparece_apagado_limpa_deleted_at(self):
        # Item foi soft-deleted numa importação anterior (deleted_at setado) e
        # reaparece com a MESMA quantidade: antes da correção, o early-continue
        # de "igual ao que já está gravado" deixava o deleted_at preso pra sempre.
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None,
                         "deleted_at": "2026-01-01T00:00:00+00:00"}
                    ],
                    "update": [{"id": "I1"}],
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo["atualizados"], 1)
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(len(atualizacoes_item), 1)
        self.assertIsNone(atualizacoes_item[0]["payload"]["deleted_at"])

    def test_item_por_unidade_com_drift_de_ponto_flutuante_nao_atualiza(self):
        # unidades é float somado/arredondado igual quantidade (peso) — precisa
        # da mesma tolerância de pesos_iguais, não de "==" exato.
        transporte_por_unidade = {
            **TRANSPORTE_NOVO,
            "itens": [
                {"sku": "128046", "quantidade": 10.0, "por_unidade": True, "unidades": 70.0, "ordens": [
                    {"fornecimento": "861886474", "ordem_venda": "", "quantidade": 10.0, "unidades": 70.0}
                ]},
            ],
        }
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": True,
                         "quantidade_pedido": 10.0, "unidades_pedido": 70.0004, "deleted_at": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_por_unidade], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes_item, [])

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

    def test_transporte_com_linha_invalida_nao_apaga_nem_zera_item_sumido(self):
        # Fix 2: transporte cuja leitura teve uma linha inválida não pode ter
        # item ausente tratado como "sumiu de verdade" — pode ter sido só a
        # linha dele que falhou o parse (ex.: célula de peso corrompida).
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None, "deleted_at": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(
            cliente, [transporte_sem_item], usuario_id="U1",
            transportes_com_linha_invalida={"5100130964"},
        )

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes, [])

    def test_transporte_com_linha_invalida_ainda_grava_itens_que_vieram_certos(self):
        # A proteção do Fix 2 só pula o passo de apagar/zerar "sumidos"; um
        # item novo/atualizado que veio certo no arquivo continua gravando.
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [], "insert": [{"id": "T1"}]},
                "transporte_itens": {"select": [], "insert": [{"id": "I1"}]},
            }
        )
        resumo = gravar_zsd106(
            cliente, [TRANSPORTE_NOVO], usuario_id="U1",
            transportes_com_linha_invalida={"5100130964"},
        )

        self.assertEqual(resumo["inseridos"], 1)

    def test_buscar_existentes_pagina_mais_de_mil_itens(self):
        # Fix 3: sem paginação, o PostgREST cortaria em 1000 linhas por
        # padrão — itens além do corte pareceriam "novos" (duplicata) e os
        # que ficaram fora escapariam da reconciliação de sumidos.
        pagina_1 = [
            {"id": f"I{i}", "transporte_id": "T1", "sku": f"SKU{i}", "separa_por_unidade": False,
             "quantidade_pedido": 1.0, "unidades_pedido": None, "deleted_at": None}
            for i in range(1000)
        ]
        pagina_2 = [
            {"id": "I1000", "transporte_id": "T1", "sku": "SKU1000", "separa_por_unidade": False,
             "quantidade_pedido": 1.0, "unidades_pedido": None, "deleted_at": None}
        ]

        def resposta_paginada(chamada):
            desde = next(f[1] for f in chamada["filtros"] if f[0] == "range")
            return pagina_1 if desde == 0 else pagina_2

        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {"select": resposta_paginada},
            }
        )
        existentes = _buscar_existentes(cliente, ["5100130964"])

        self.assertEqual(len(existentes["5100130964"]["itens"]), 1001)
        chamadas_range = [
            c for c in cliente.chamadas
            if c["tabela"] == "transporte_itens" and any(f[0] == "range" for f in c["filtros"])
        ]
        self.assertEqual(len(chamadas_range), 2)
        self.assertIn(("range", 0, 999), chamadas_range[0]["filtros"])
        self.assertIn(("range", 1000, 1999), chamadas_range[1]["filtros"])

    def test_insert_transporte_sem_retorno_levanta_erro_claro(self):
        # Fix 4: sob RLS, um INSERT negado volta HTTP 200 com data vazio — não
        # pode virar um "inserido" silencioso no resumo.
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [], "insert": []},
            }
        )
        with self.assertRaises(RuntimeError):
            gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

    def test_insert_item_sem_retorno_levanta_erro_claro(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [], "insert": [{"id": "T1"}]},
                "transporte_itens": {"select": [], "insert": []},
            }
        )
        with self.assertRaises(RuntimeError):
            gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

    def test_update_item_sem_retorno_levanta_erro_claro(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 5.0, "unidades_pedido": None, "deleted_at": None}
                    ],
                    "update": [],
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        with self.assertRaises(RuntimeError):
            gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

    def test_update_exclusao_sem_retorno_levanta_erro_claro(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None, "deleted_at": None}
                    ],
                    "update": [],
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        with self.assertRaises(RuntimeError):
            gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")


if __name__ == "__main__":
    unittest.main()
