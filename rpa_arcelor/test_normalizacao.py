import unittest
from normalizacao import (
    remover_zeros_esquerda, normalizar_cabecalho, mapear_colunas,
    mapear_coluna_opcional, arredondar_peso, pesos_iguais,
    parse_peso_extrato, parse_numero_zsd106,
)


class TestRemoverZerosEsquerda(unittest.TestCase):
    def test_remove_zeros_do_meio_de_codigo_numerico(self):
        self.assertEqual(remover_zeros_esquerda("0015444609"), "15444609")

    def test_mantem_string_sem_zero_a_esquerda(self):
        self.assertEqual(remover_zeros_esquerda("15444609"), "15444609")

    def test_nao_mexe_em_zero_sozinho(self):
        self.assertEqual(remover_zeros_esquerda("0"), "0")


class TestNormalizarCabecalho(unittest.TestCase):
    def test_ignora_acento_caixa_ordinal_e_espaco(self):
        self.assertEqual(normalizar_cabecalho("  N Transporte "), "N TRANSPORTE")
        self.assertEqual(normalizar_cabecalho("N° Transporte"), "N TRANSPORTE")
        self.assertEqual(normalizar_cabecalho("Região"), "REGIAO")


class TestMapearColunas(unittest.TestCase):
    def test_casa_por_normalizacao(self):
        mapa = mapear_colunas(["  N Transporte ", "material"], ["N° Transporte", "Material"])
        self.assertEqual(mapa["N° Transporte"], "  N Transporte ")
        self.assertEqual(mapa["Material"], "material")

    def test_levanta_erro_citando_o_que_falta(self):
        with self.assertRaises(ValueError) as ctx:
            mapear_colunas(["Fornecimento"], ["N° Transporte", "Material"])
        self.assertIn("N° Transporte", str(ctx.exception))
        self.assertIn("Material", str(ctx.exception))

    def test_coluna_opcional_devolve_none_quando_falta(self):
        self.assertIsNone(mapear_coluna_opcional(["Material"], "Fornecimento"))
        self.assertEqual(mapear_coluna_opcional(["Fornecimento"], "fornecimento"), "Fornecimento")


class TestPeso(unittest.TestCase):
    def test_arredonda_para_grama(self):
        self.assertEqual(arredondar_peso(0.1 + 0.2), 0.3)

    def test_pesos_iguais_tolera_meia_grama(self):
        self.assertTrue(pesos_iguais(100.0004, 100.0))
        self.assertFalse(pesos_iguais(100.001, 100.0))

    def test_parse_peso_extrato_ponto_milhar_virgula_decimal(self):
        self.assertEqual(parse_peso_extrato("        1.205"), 1205.0)
        self.assertEqual(parse_peso_extrato("73"), 73.0)
        self.assertEqual(parse_peso_extrato("112,86"), 112.86)

    def test_parse_peso_extrato_vazio_vira_zero(self):
        self.assertEqual(parse_peso_extrato(""), 0.0)

    def test_parse_numero_zsd106_com_virgula_ponto_e_milhar(self):
        self.assertEqual(parse_numero_zsd106("1.150,86"), 1150.86)

    def test_parse_numero_zsd106_sem_virgula_ponto_e_decimal(self):
        self.assertEqual(parse_numero_zsd106("112.86"), 112.86)
        self.assertEqual(parse_numero_zsd106("1150"), 1150.0)

    def test_parse_numero_zsd106_ambiguo_sem_virgula_levanta_erro(self):
        # "1.496" sem vírgula bate com o padrão de milhar do Excel (grupos de
        # 3 dígitos após o ponto) — pode ser 1.496 ou 1496, não dá pra
        # adivinhar com segurança contra um formato de SAP ainda não validado.
        with self.assertRaises(ValueError):
            parse_numero_zsd106("1.496")

    def test_parse_numero_zsd106_casos_nao_ambiguos_continuam_ok(self):
        # Com vírgula, nunca é ambíguo (ponto é milhar, vírgula é decimal).
        self.assertEqual(parse_numero_zsd106("1.150,86"), 1150.86)
        # Decimal comum (não bate no padrão de milhar: menos de 3 dígitos
        # depois do ponto) continua parseando normalmente.
        self.assertEqual(parse_numero_zsd106("112.86"), 112.86)


if __name__ == "__main__":
    unittest.main()
