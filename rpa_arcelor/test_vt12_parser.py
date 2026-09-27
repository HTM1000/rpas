# -*- coding: utf-8 -*-
import unittest
from vt12_parser import parse_vt12

# Recorte real de vt12.txt (dois transportes, cada um com fornecimentos).
AMOSTRA = """
Transportes e fornecimento\t\t\tID ext.1\tStMvMercGl\tLoc.exped.\tStGlbPickg\tRec.merc.\tEnderDest.\tRegião\tIncoterms\tPeso total/KG\tTp.exped.\tDt.remessa\tDta.pln.SM\tCentro\tStatusGlob\tForncServ.
\t5100133088\t\tSP CAPITAL 18.09\t\t\t\t\t\t\t\t        6.940\t01\t\t\t\t\tLOGHIS LOGISTICA E SERVICOS
\t\t0862038375\t\tA\t9728\tA\tSPECIAL TUBOS E ACOS LTDA\tBR 07041-030 GUARULHOS\tSP\tCIF\t          500\t08\t16.09.2026\t16.09.2026\t9728
\t\t0862035007\t\tC\t9728\tC\tRODRIGO DA CORTE DE ABREU IN\tBR 07210-380 GUARULHOS\tSP\tCIF\t        1.205\t08\t15.09.2026\t15.09.2026\t9728
\t5100133089\t\tSP CAPITAL 18.09\t\t\t\t\t\t\t\t        5.566\t01\t\t\t\t\tLOGHIS LOGISTICA E SERVICOS
\t\t0862042917\t\tA\t9728\tA\tGRANEI METALURGICA  AUTO PEC\tBR 07140-237 GUARULHOS\tSP\tCIF\t          200\t08\t16.09.2026\t16.09.2026\t9728
""".strip("\n").splitlines()


class TestParseVt12(unittest.TestCase):
    def test_agrupa_fornecimentos_por_transporte(self):
        transportes, invalidas = parse_vt12(AMOSTRA)
        self.assertEqual(invalidas, [])
        self.assertEqual(len(transportes), 2)
        self.assertEqual(transportes[0]["numero_transporte"], "5100133088")
        self.assertEqual(transportes[0]["rota"], "SP CAPITAL 18.09")
        self.assertEqual(transportes[0]["transportadora"], "LOGHIS LOGISTICA E SERVICOS")
        self.assertEqual(len(transportes[0]["fornecimentos"]), 2)

    def test_remove_zero_a_esquerda_do_fornecimento(self):
        transportes, _ = parse_vt12(AMOSTRA)
        fornecimentos = [f["fornecimento"] for f in transportes[0]["fornecimentos"]]
        self.assertIn("862038375", fornecimentos)
        self.assertNotIn("0862038375", fornecimentos)

    def test_ordem_de_carregamento_e_invertida(self):
        # A ÚLTIMA linha do transporte no arquivo é a PRIMEIRA a carregar.
        transportes, _ = parse_vt12(AMOSTRA)
        por_fornecimento = {f["fornecimento"]: f["ordem_carregamento"] for f in transportes[0]["fornecimentos"]}
        self.assertEqual(por_fornecimento["862035007"], 1)  # última linha do arquivo pro transporte 1
        self.assertEqual(por_fornecimento["862038375"], 2)

    def test_le_cliente_destino_uf_peso(self):
        transportes, _ = parse_vt12(AMOSTRA)
        f = next(f for f in transportes[0]["fornecimentos"] if f["fornecimento"] == "862038375")
        self.assertEqual(f["cliente"], "SPECIAL TUBOS E ACOS LTDA")
        self.assertEqual(f["destino"], "BR 07041-030 GUARULHOS")
        self.assertEqual(f["uf"], "SP")
        self.assertEqual(f["peso_kg"], 500.0)

    def test_fornecimento_solto_sem_transporte_acima_vira_invalida(self):
        linhas_quebradas = ["Transportes e fornecimento", "\t\t0862038375\t\tA\t9728\tA\tX\tY\tSP\tCIF\t500"]
        transportes, invalidas = parse_vt12(linhas_quebradas)
        self.assertEqual(transportes, [])
        self.assertEqual(len(invalidas), 1)
        self.assertIn("862038375", invalidas[0])

    def test_levanta_erro_se_nao_reconhecer_o_titulo(self):
        with self.assertRaises(ValueError):
            parse_vt12(["qualquer coisa", "sem o titulo certo"])


if __name__ == "__main__":
    unittest.main()
