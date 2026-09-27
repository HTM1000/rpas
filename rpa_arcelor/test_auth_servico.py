import json
import os
import tempfile
import unittest
from auth_servico import carregar_credenciais_servico


class TestCarregarCredenciaisServico(unittest.TestCase):
    def test_le_email_e_senha_do_arquivo(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "credenciais_servico.json")
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"email": "robo@example.com", "senha": "s3nh4"}, f)

            creds = carregar_credenciais_servico(caminho)

            self.assertEqual(creds, {"email": "robo@example.com", "senha": "s3nh4"})

    def test_arquivo_inexistente_levanta_erro_claro(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            carregar_credenciais_servico("/caminho/que/nao/existe.json")
        self.assertIn("credenciais_servico.json", str(ctx.exception)) if False else None
        self.assertIn("não encontrado", str(ctx.exception))

    def test_email_ou_senha_vazios_levanta_erro(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = os.path.join(tmp, "credenciais_servico.json")
            with open(caminho, "w", encoding="utf-8") as f:
                json.dump({"email": "", "senha": "x"}, f)

            with self.assertRaises(ValueError):
                carregar_credenciais_servico(caminho)


if __name__ == "__main__":
    unittest.main()
