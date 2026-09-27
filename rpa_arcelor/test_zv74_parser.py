import unittest
from zv74_parser import parse_zv74

CABECALHO = ["Desc Cond Pagto", "Ordem Vendas", "Número do fornecimento", "Texto Embarque", "Texto Embarque"]


class TestParseZv74(unittest.TestCase):
    def test_le_observacao_e_condicao_pagamento(self):
        r = parse_zv74(
            [
                CABECALHO,
                ["A Prazo - 30/40/50/60 dd", "0201308660", "0846252364", " ENVIAR EXATAMENTE 300 BARRAS", ""],
            ]
        )
        self.assertEqual(r["observacoes"], [{"fornecimento": "846252364", "texto": "ENVIAR EXATAMENTE 300 BARRAS"}])
        self.assertEqual(r["condicoes_pagamento"], [{"ordem_venda": "201308660", "descricao": "A Prazo - 30/40/50/60 dd"}])

    def test_linha_sem_texto_e_contada_e_descartada(self):
        r = parse_zv74([CABECALHO, ["Venda prazo boleto 21 dd", "0201303446", "", "", ""]])
        self.assertEqual(r["observacoes"], [])
        self.assertEqual(r["linhas_sem_texto"], 1)
        # Mas a condição de pagamento vem em TODA linha, mesmo sem fornecimento.
        self.assertEqual(r["condicoes_pagamento"], [{"ordem_venda": "201303446", "descricao": "Venda prazo boleto 21 dd"}])

    def test_linha_com_texto_sem_fornecimento_e_contada_e_descartada(self):
        r = parse_zv74([CABECALHO, ["X", "1", "", "algum texto", ""]])
        self.assertEqual(r["observacoes"], [])
        self.assertEqual(r["linhas_sem_fornecimento"], 1)

    def test_primeira_ocorrencia_manda_na_repeticao(self):
        r = parse_zv74(
            [
                CABECALHO,
                ["A", "1", "0846252364", "primeiro texto", ""],
                ["B", "1", "0846252364", "segundo texto (ignorado)", ""],
            ]
        )
        self.assertEqual(r["observacoes"], [{"fornecimento": "846252364", "texto": "primeiro texto"}])
        self.assertEqual(r["condicoes_pagamento"], [{"ordem_venda": "1", "descricao": "A"}])

    def test_usa_a_primeira_coluna_texto_embarque_preenchida_entre_as_duas(self):
        r = parse_zv74([CABECALHO, ["A", "1", "0846252364", "", "segunda coluna preenchida"]])
        self.assertEqual(r["observacoes"], [{"fornecimento": "846252364", "texto": "segunda coluna preenchida"}])

    def test_aceita_arquivo_sem_as_colunas_de_condicao_pagamento(self):
        cabecalho_antigo = ["Número do fornecimento", "Texto Embarque"]
        r = parse_zv74([cabecalho_antigo, ["0846252364", "texto"]])
        self.assertEqual(r["observacoes"], [{"fornecimento": "846252364", "texto": "texto"}])
        self.assertEqual(r["condicoes_pagamento"], [])

    def test_levanta_erro_se_faltar_fornecimento_ou_texto(self):
        with self.assertRaises(ValueError):
            parse_zv74([["Só Isso"], ["valor"]])

    def test_devolve_vazio_para_planilha_sem_linhas(self):
        self.assertEqual(
            parse_zv74([]),
            {"observacoes": [], "condicoes_pagamento": [], "linhas_sem_texto": 0, "linhas_sem_fornecimento": 0},
        )


if __name__ == "__main__":
    unittest.main()
