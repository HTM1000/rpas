# -*- coding: utf-8 -*-
import unittest
from zsd106_parser import parse_zsd106

COLUNAS = ["N° Transporte", "Doc. Modelo", "Fornecimento", "Material", "Quantidade", "Qtde"]


def linha(transporte, material, peso, fornecimento="", ordem_venda="", unidades=None):
    """Uma linha do export. Sem `unidades`, item por peso (Quantidade == Qtde)."""
    return {
        "N° Transporte": str(transporte),
        "Doc. Modelo": str(ordem_venda),
        "Fornecimento": str(fornecimento),
        "Material": str(material),
        "Quantidade": str(unidades if unidades is not None else peso),
        "Qtde": str(peso),
    }


class TestParseZsd106(unittest.TestCase):
    def test_agrupa_linhas_do_mesmo_transporte_como_itens_dele(self):
        transportes, invalidas = parse_zsd106(
            [
                linha(5100130964, 128046, 10, fornecimento="0861886474"),
                linha(5100130964, 101938, 109.41, fornecimento="0861918336"),
                linha(5100130907, 101894, 70, fornecimento="0861884780"),
            ],
            COLUNAS,
        )
        self.assertEqual(invalidas, [])
        self.assertEqual(len(transportes), 2)
        self.assertEqual(transportes[0]["numero_transporte"], "5100130964")
        self.assertEqual([i["sku"] for i in transportes[0]["itens"]], ["128046", "101938"])
        self.assertEqual(transportes[1]["numero_transporte"], "5100130907")

    def test_quantidade_igual_a_qtde_e_por_peso_diferente_e_por_unidade(self):
        transportes, _ = parse_zsd106(
            [
                linha(1, "249901", 1496),
                linha(1, "101802", 518.28, unidades=70),
            ],
            COLUNAS,
        )
        self.assertEqual(
            transportes[0]["itens"],
            [
                {"sku": "249901", "quantidade": 1496.0, "por_unidade": False, "unidades": None, "ordens": []},
                {
                    "sku": "101802", "quantidade": 518.28, "por_unidade": True, "unidades": 70.0,
                    "ordens": [],
                },
            ],
        )

    def test_tira_zeros_a_esquerda_do_material(self):
        transportes, _ = parse_zsd106([linha(1, "000000000000101802", 10)], COLUNAS)
        self.assertEqual(transportes[0]["itens"][0]["sku"], "101802")

    def test_soma_mesmo_material_em_fornecimentos_diferentes_mesma_forma(self):
        transportes, _ = parse_zsd106(
            [
                linha(1, 107163, 85.2, fornecimento=1),
                linha(1, 107163, 12.3, fornecimento=2),
            ],
            COLUNAS,
        )
        self.assertEqual(len(transportes[0]["itens"]), 1)
        item = transportes[0]["itens"][0]
        self.assertEqual(item["quantidade"], 97.5)
        self.assertEqual(
            item["ordens"],
            [
                {"fornecimento": "1", "ordem_venda": "", "quantidade": 85.2, "unidades": None},
                {"fornecimento": "2", "ordem_venda": "", "quantidade": 12.3, "unidades": None},
            ],
        )

    def test_mantem_separado_mesmo_material_por_peso_e_por_unidade(self):
        transportes, _ = parse_zsd106(
            [
                linha(1, 101802, 500, fornecimento=1),
                linha(1, 101802, 518.28, fornecimento=2, unidades=70),
            ],
            COLUNAS,
        )
        self.assertEqual(len(transportes[0]["itens"]), 2)
        self.assertFalse(transportes[0]["itens"][0]["por_unidade"])
        self.assertTrue(transportes[0]["itens"][1]["por_unidade"])

    def test_remove_zero_a_esquerda_de_fornecimento_e_ordem_venda(self):
        # Decisão deste projeto: diferente do front hoje, o robô tira o zero
        # também aqui, pra casar com VT12/ZV74.
        transportes, _ = parse_zsd106(
            [linha(1, 209260, 1010, fornecimento="0861653306", ordem_venda="0202878251")], COLUNAS
        )
        ordem = transportes[0]["itens"][0]["ordens"][0]
        self.assertEqual(ordem["fornecimento"], "861653306")
        self.assertEqual(ordem["ordem_venda"], "202878251")

    def test_recusa_linha_sem_material_ou_com_quantidade_nao_positiva(self):
        transportes, invalidas = parse_zsd106(
            [
                linha(1, "", 10, fornecimento=1),
                linha(1, 128046, 0),
                linha(1, 128046, 10, unidades=-5),
                linha(1, 128046, 10),  # válida
            ],
            COLUNAS,
        )
        self.assertEqual(len(invalidas), 3)
        self.assertIn("Material vazio", invalidas[0])
        self.assertIn("Qtde inválida", invalidas[1])
        self.assertIn("Quantidade inválida", invalidas[2])
        self.assertEqual(len(transportes[0]["itens"]), 1)

    def test_pula_linha_sem_transporte_e_linha_de_total(self):
        transportes, invalidas = parse_zsd106(
            [
                linha(5100132384, 128046, 10, fornecimento=1),
                linha("", 128046, 999),
                linha(5100132384, "", 2879.466, unidades=2041),
            ],
            COLUNAS,
        )
        self.assertEqual(invalidas, [])
        self.assertEqual(len(transportes), 1)
        self.assertEqual(transportes[0]["linhas_arquivo"], 1)

    def test_aceita_planilha_sem_fornecimento_nem_doc_modelo(self):
        linha_sem_extra = {"N° Transporte": "1", "Material": "128046", "Quantidade": "10", "Qtde": "10"}
        transportes, invalidas = parse_zsd106(
            [linha_sem_extra], ["N° Transporte", "Material", "Quantidade", "Qtde"]
        )
        self.assertEqual(invalidas, [])
        self.assertEqual(transportes[0]["itens"][0]["ordens"], [])

    def test_recusa_planilha_sem_as_colunas_obrigatorias(self):
        with self.assertRaises(ValueError):
            parse_zsd106([], ["Fornecimento", "Nome"])

    def test_junta_fornecimentos_sem_repetir_na_ordem_do_arquivo(self):
        transportes, _ = parse_zsd106(
            [
                linha(1, "A", 10, fornecimento=861886474),
                linha(1, "B", 10, fornecimento=861886474),
                linha(1, "A", 5, fornecimento=861918336),
            ],
            COLUNAS,
        )
        self.assertEqual(transportes[0]["fornecimentos"], ["861886474", "861918336"])


if __name__ == "__main__":
    unittest.main()
