# rpa_arcelor/test_vt12_writer.py
import unittest
from supabase_fake import FakeSupabaseClient
from vt12_writer import gravar_vt12

TRANSPORTE = {
    "numero_transporte": "5100133088",
    "rota": "SP CAPITAL 18.09",
    "transportadora": "LOGHIS",
    "fornecimentos": [
        {"fornecimento": "862035007", "ordem_carregamento": 1, "cliente": "RODRIGO", "destino": "BR ...", "uf": "SP", "peso_kg": 1205.0},
        {"fornecimento": "862038375", "ordem_carregamento": 2, "cliente": "SPECIAL", "destino": "BR ...", "uf": "SP", "peso_kg": 500.0},
    ],
}


class TestGravarVt12(unittest.TestCase):
    def test_apaga_e_insere_por_transporte(self):
        cliente = FakeSupabaseClient(
            respostas={"transportes": {"select": [{"id": "T1", "numero_transporte": "5100133088"}]}}
        )
        resumo = gravar_vt12(cliente, [TRANSPORTE])

        self.assertEqual(resumo, {"transportes_gravados": 1, "transportes_sem_cadastro": 0})
        deletes = [c for c in cliente.chamadas if c["tabela"] == "arc_transporte_fornecimento" and c["operacao"] == "delete"]
        inserts = [c for c in cliente.chamadas if c["tabela"] == "arc_transporte_fornecimento" and c["operacao"] == "insert"]
        self.assertEqual(len(deletes), 1)
        self.assertEqual(deletes[0]["filtros"], [("eq", "transporte_id", "T1")])
        self.assertEqual(len(inserts[0]["payload"]), 2)
        self.assertEqual(inserts[0]["payload"][0]["transporte_id"], "T1")
        self.assertEqual(inserts[0]["payload"][0]["fornecimento"], "862035007")

    def test_transporte_sem_cadastro_no_banco_e_contado_e_pulado(self):
        cliente = FakeSupabaseClient(respostas={"transportes": {"select": []}})
        resumo = gravar_vt12(cliente, [TRANSPORTE])

        self.assertEqual(resumo, {"transportes_gravados": 0, "transportes_sem_cadastro": 1})
        mexeu = [c for c in cliente.chamadas if c["tabela"] == "arc_transporte_fornecimento"]
        self.assertEqual(mexeu, [])


if __name__ == "__main__":
    unittest.main()
