# -*- coding: utf-8 -*-
"""Parser do VT12 (sequência de carregamento, export de texto tab-separated do
SAP) — espelha wmsarcelormital/src/lib/sequenciaCarregamentoParser.ts,
inclusive a ordem invertida (a última linha do transporte no arquivo é a
PRIMEIRA a entrar no caminhão)."""
from normalizacao import remover_zeros_esquerda, parse_peso_extrato

COL_TRANSPORTE = 1
COL_FORNECIMENTO = 2
COL_ROTA = 3
COL_CLIENTE = 7
COL_DESTINO = 8
COL_UF = 9
COL_PESO = 11
COL_TRANSPORTADORA = 17

TITULO = "Transportes e fornecimento"


def ler_linhas_vt12(caminho: str) -> list:
    """Lê o export do VT12: texto tab-separated, ISO-8859-1 (Latin-1) ou
    UTF-16 com BOM — mesma decodificação de `Arcelor_WMS.ler_planilha`."""
    with open(caminho, "rb") as f:
        raw = f.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16").splitlines()
    return raw.decode("latin-1", errors="ignore").splitlines()


def parse_vt12(linhas_texto: list) -> tuple:
    if not any(TITULO in linha for linha in linhas_texto):
        raise ValueError(f'Arquivo não reconhecido: não encontrei o título "{TITULO}" da sequência de carregamento.')

    transportes = []
    linhas_invalidas = []
    atual = None

    for i, linha in enumerate(linhas_texto):
        if not linha.strip():
            continue
        campos = linha.split("\t")

        def campo(idx):
            return campos[idx].strip() if idx < len(campos) else ""

        numero_transporte = remover_zeros_esquerda(campo(COL_TRANSPORTE))
        if numero_transporte:
            atual = {
                "numero_transporte": numero_transporte,
                "rota": campo(COL_ROTA),
                "transportadora": campo(COL_TRANSPORTADORA),
                "fornecimentos": [],
            }
            transportes.append(atual)
            continue

        fornecimento = remover_zeros_esquerda(campo(COL_FORNECIMENTO))
        if not fornecimento:
            continue

        if atual is None:
            linhas_invalidas.append(f"Linha {i + 1}: fornecimento {fornecimento} sem transporte acima.")
            continue

        atual["fornecimentos"].append(
            {
                "fornecimento": fornecimento,
                "cliente": campo(COL_CLIENTE),
                "destino": campo(COL_DESTINO),
                "uf": campo(COL_UF),
                "peso_kg": parse_peso_extrato(campo(COL_PESO)),
            }
        )

    for t in transportes:
        invertidos = list(reversed(t["fornecimentos"]))
        for idx, f in enumerate(invertidos):
            f["ordem_carregamento"] = idx + 1
        t["fornecimentos"] = invertidos

    return transportes, linhas_invalidas
