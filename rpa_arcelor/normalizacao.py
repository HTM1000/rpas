# -*- coding: utf-8 -*-
"""Normalização compartilhada pelos 3 parsers do RPA Arcelor (ZSD106, VT12,
ZV74). Espelha wmsarcelormital/src/lib/transporteImportParsers.ts e
src/lib/peso.ts — mesmas regras, pra não gravar em desacordo com o que o front
já grava."""
import re
import unicodedata

PESO_MINIMO = 0.001


def remover_zeros_esquerda(valor: str) -> str:
    """'0015444609' -> '15444609'. Espelha removerZerosEsquerda do front."""
    return re.sub(r"^0+(?=\d)", "", valor.strip())


def normalizar_cabecalho(valor: str) -> str:
    """Sem acento, sem º/°, espaço colapsado, maiúsculo. Espelha normalizarCabecalho."""
    sem_acento = unicodedata.normalize("NFD", valor)
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    sem_ordinal = re.sub(r"[º°]", "", sem_acento)
    return re.sub(r"\s+", " ", sem_ordinal).strip().upper()


def mapear_coluna_opcional(colunas_planilha, esperado: str):
    """Casa um cabeçalho esperado com o real da planilha por normalização;
    devolve None (em vez de levantar erro) quando não existe — para colunas
    que só alimentam informação extra."""
    normalizado_para_real = {normalizar_cabecalho(str(c)): c for c in colunas_planilha}
    return normalizado_para_real.get(normalizar_cabecalho(esperado))


def mapear_colunas(colunas_planilha, esperadas):
    """Como mapear_coluna_opcional, mas para colunas OBRIGATÓRIAS: levanta
    ValueError citando todas as que faltaram."""
    resultado = {}
    faltando = []
    for esperado in esperadas:
        real = mapear_coluna_opcional(colunas_planilha, esperado)
        if real is None:
            faltando.append(esperado)
        else:
            resultado[esperado] = real
    if faltando:
        raise ValueError(
            f"Colunas não encontradas na planilha: {faltando}. "
            f"Colunas disponíveis: {list(colunas_planilha)}"
        )
    return resultado


def arredondar_peso(valor: float) -> float:
    """Arredonda pra grama, evitando lixo de ponto flutuante ao somar. Espelha arredondarPeso."""
    return round(valor * 1000) / 1000


def pesos_iguais(a, b) -> bool:
    """Tolerância de meia grama. Espelha pesosIguais."""
    return abs((a or 0) - (b or 0)) < PESO_MINIMO / 2


def parse_peso_extrato(valor: str) -> float:
    """'        1.205' -> 1205.0; '73' -> 73.0. Ponto é separador de milhar,
    vírgula é decimal — formato dos extratos de texto do SAP (VT12). Espelha
    pesoDoExtrato."""
    limpo = re.sub(r"\s", "", valor).replace(".", "").replace(",", ".")
    if not limpo:
        return 0.0
    try:
        return arredondar_peso(float(limpo))
    except ValueError:
        return 0.0


def parse_numero_zsd106(valor: str) -> float:
    """Aceita vírgula decimal brasileira ('1.150,86') OU ponto decimal já
    convertido (ex.: pandas lendo um .xlsx real de verdade, '112.86' sem
    separador de milhar) — o formato real do export do ZSD106 ainda não foi
    validado em SAP (ver CLAUDE.md do rpa_arcelor). Se a string tiver vírgula,
    ponto é milhar; senão, ponto é decimal."""
    texto = valor.strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return float(texto)
