# -*- coding: utf-8 -*-
"""Autenticação de serviço do robô — sem tela de login, sem o operador digitar
nada. Credenciais fixas de uma conta com role 'conferente' já atribuída."""
import json
import os


def carregar_credenciais_servico(caminho: str) -> dict:
    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"Arquivo de credenciais do robô não encontrado: {caminho}. "
            'Crie o arquivo com {"email": "...", "senha": "..."} antes de rodar '
            "(veja credenciais_servico.example.json)."
        )
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    email = str(dados.get("email", "")).strip()
    senha = str(dados.get("senha", "")).strip()
    if not email or not senha:
        raise ValueError(f"{caminho} precisa ter 'email' e 'senha' preenchidos.")
    return {"email": email, "senha": senha}
