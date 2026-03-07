#!/usr/bin/env python3
"""Script para reduzir o delay entre_cliques no config.json"""

import json

def atualizar_config():
    # Ler config.json
    with open("essential/config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

    # Atualizar entre_cliques
    config["tempos_espera"]["entre_cliques"] = 1.5

    # Salvar config.json
    with open("essential/config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("Config atualizado com sucesso!")
    print("  - entre_cliques: 3s -> 1.5s")

if __name__ == "__main__":
    atualizar_config()
