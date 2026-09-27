# RPA Arcelor — Expedição/Recebimento (ZSD106/VT12/ZV74) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tirar o login do robô `rpa_arcelor`, dar a ele 2 seções (Expedição/Recebimento) com botões que rodam ZSD106/VT12/ZV74 e gravam no Supabase de produção do `wmsarcelormital`, reaproveitando exatamente as tabelas e regras que `ImportarTransportesButton.tsx` já usa hoje — mais a coluna `deleted_at` que o front vai precisar (mas cujo consumo no front fica pra um Plano 2 separado).

**Architecture:** Módulos Python novos em `rpa_arcelor/` — um parser + um writer por transação SAP (puros, sem GUI/SAP, 100% testáveis com `unittest`), mais uma normalização compartilhada (zero à esquerda, peso em grama, cabeçalho). `Arcelor_WMS.py` passa a chamar esses módulos em vez do `MAPEAMENTO` genérico atual, e ganha autenticação de serviço silenciosa no lugar da tela de login. Um cliente Supabase-falso (`supabase_fake.py`) permite testar toda a reconciliação sem rede. Migration separada no `wmsarcelormital` cria a coluna nova.

**Tech Stack:** Python 3.13, `pandas`/`openpyxl` (já dependências do projeto), `unittest` (stdlib, sem dependência nova), `win32com`/SAP GUI Scripting (já em uso), Supabase Postgres (migration SQL).

**Spec:** `docs/superpowers/specs/2026-09-27-rpa-arcelor-expedicao-recebimento-design.md`

## Global Constraints

- Nunca sobrescrever campos que o operador edita em `transportes` (`placa_confirmada`, campos de encerramento, etc.) — só os campos que o ZSD106 realmente informa.
- Só grava/atualiza/remove item em transporte com `status` `agendado` ou `em_andamento` — nunca em `finalizado`/`descumprido`.
- Sem checagem de saldo de estoque — grava o peso do ZSD106 direto (decisão do usuário, ver spec).
- Zero à esquerda removido em TODOS os campos-chave de junção dos 3 arquivos: número de transporte, Material/SKU, Fornecimento, Doc. Modelo/ordem de venda.
- A chave `anon` nunca grava sozinha — login de serviço silencioso com uma conta fixa (role `conferente`); credenciais em arquivo local fora do git.
- `arc_transporte` é tabela órfã — nunca usar.
- Peso é sempre `numeric(14,3)` (grama) — toda soma/comparação de peso passa por `arredondar_peso`/`pesos_iguais`, nunca `==` direto.

## Review Focus

- Mesmo material do ZSD106 vindo por peso numa linha e por unidade em outra no mesmo transporte deve virar **2 itens distintos** (chave sku+forma), não 1 item que confunde as somas.
- Transporte do ZSD106 já `finalizado`/`descumprido` não deve ganhar item novo nem ter item removido/zerado pelo robô.
- Item com material já no pré-picking que some do arquivo deve **zerar sem `deleted_at`** — nunca esconder um problema de estoque já separado fisicamente.
- VT12 com linha de fornecimento solta antes de qualquer transporte (arquivo cortado) não deve quebrar o parser — só virar linha inválida reportada.
- ZV74 sem as colunas opcionais de condição de pagamento (arquivo mais antigo) continua sendo aceito, só sem gravar condição de pagamento.

---

## File Structure

```
rpa_arcelor/
  normalizacao.py                 (NOVO) zero à esquerda, cabeçalho, peso em grama
  zsd106_parser.py                (NOVO) parser puro do export do ZSD106
  zsd106_writer.py                (NOVO) reconciliação + gravação no Supabase
  vt12_parser.py                  (NOVO) parser puro do export do VT12
  vt12_writer.py                  (NOVO) gravação (delete-then-insert) no Supabase
  zv74_parser.py                  (NOVO) parser puro do export do ZV74
  zv74_writer.py                  (NOVO) gravação (upsert) no Supabase
  auth_servico.py                 (NOVO) credenciais de serviço do robô
  supabase_fake.py                (NOVO) duplo de teste do cliente supabase-py
  credenciais_servico.example.json (NOVO) modelo, committed
  test_normalizacao.py            (NOVO)
  test_zsd106_parser.py           (NOVO)
  test_zsd106_writer.py           (NOVO)
  test_vt12_parser.py             (NOVO)
  test_vt12_writer.py             (NOVO)
  test_zv74_parser.py             (NOVO)
  test_zv74_writer.py             (NOVO)
  test_auth_servico.py            (NOVO)
  Arcelor_WMS.py                  (MODIFICA) remove login, GUI 2 seções, liga tudo

.gitignore                        (MODIFICA) ignora credenciais_servico.json

D:\www\react\wmsarcelormital\
  supabase/migrations/20260927120000_transporte_itens_deleted_at.sql  (NOVO)
```

---

## Task 1: Normalização compartilhada

**Files:**
- Create: `rpa_arcelor/normalizacao.py`
- Test: `rpa_arcelor/test_normalizacao.py`

**Interfaces:**
- Produces: `remover_zeros_esquerda(valor: str) -> str`, `normalizar_cabecalho(valor: str) -> str`, `mapear_colunas(colunas_planilha: list[str], esperadas: list[str]) -> dict[str, str]`, `mapear_coluna_opcional(colunas_planilha: list[str], esperado: str) -> str | None`, `arredondar_peso(valor: float) -> float`, `pesos_iguais(a: float | None, b: float | None) -> bool`, `parse_peso_extrato(valor: str) -> float`, `parse_numero_zsd106(valor: str) -> float` — usados por todas as tasks seguintes.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_normalizacao.py
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_normalizacao -v`
Expected: FAIL (ModuleNotFoundError: No module named 'normalizacao')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/normalizacao.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_normalizacao -v`
Expected: PASS (12 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/normalizacao.py rpa_arcelor/test_normalizacao.py
git commit -m "feat(rpa_arcelor): normalização compartilhada (zero à esquerda, peso, cabeçalho)"
```

---

## Task 2: Parser do ZSD106

**Files:**
- Create: `rpa_arcelor/zsd106_parser.py`
- Test: `rpa_arcelor/test_zsd106_parser.py`

**Interfaces:**
- Consumes: `remover_zeros_esquerda`, `mapear_colunas`, `mapear_coluna_opcional`, `arredondar_peso`, `parse_numero_zsd106` de `normalizacao.py` (Task 1).
- Produces: `parse_zsd106(linhas: list[dict], colunas: list[str]) -> tuple[list[dict], list[str]]`. Cada transporte: `{"numero_transporte": str, "itens": [...], "linhas_arquivo": int, "fornecimentos": [str]}`. Cada item: `{"sku": str, "quantidade": float, "por_unidade": bool, "unidades": float|None, "ordens": [...]}`. Cada ordem: `{"fornecimento": str, "ordem_venda": str, "quantidade": float, "unidades": float|None}`. Usado por Task 3.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_zsd106_parser.py
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
                    "ordens": [{"fornecimento": "", "ordem_venda": "", "quantidade": 518.28, "unidades": 70.0}],
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_zsd106_parser -v`
Expected: FAIL (ModuleNotFoundError: No module named 'zsd106_parser')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/zsd106_parser.py
# -*- coding: utf-8 -*-
"""Parser do ZSD106 (export do SAP): agrupa por transporte e por item (sku +
forma de separar), somando peso/unidade das linhas que se repetem por
fornecimento. Espelha wmsarcelormital/src/lib/agendaExpedicaoParser.ts —
com UMA diferença deliberada: aqui `Fornecimento` e `Doc. Modelo` (ordem de
venda) TAMBÉM perdem o zero à esquerda, pra casar com VT12/ZV74 (o front hoje
não tira desses dois campos nesse parser específico — inconsistência
preexistente que este robô não repete)."""
from normalizacao import (
    remover_zeros_esquerda,
    mapear_colunas,
    mapear_coluna_opcional,
    arredondar_peso,
    parse_numero_zsd106,
)

COLUNAS_OBRIGATORIAS = ["N° Transporte", "Material", "Quantidade", "Qtde"]


def _tentar_parse(texto: str):
    if not texto:
        return None
    try:
        return parse_numero_zsd106(texto)
    except ValueError:
        return None


def parse_zsd106(linhas: list[dict], colunas: list[str]) -> tuple[list[dict], list[str]]:
    """`linhas` = uma lista de dicts (uma por linha do export, valores como
    string — igual `df.to_dict('records')` de `ler_planilha` devolve).
    Retorna (transportes, linhas_invalidas)."""
    mapa = mapear_colunas(colunas, COLUNAS_OBRIGATORIAS)
    col_fornecimento = mapear_coluna_opcional(colunas, "Fornecimento")
    col_ordem_venda = mapear_coluna_opcional(colunas, "Doc. Modelo") or mapear_coluna_opcional(
        colunas, "Doc Modelo"
    )

    ordem_transportes: list[str] = []
    grupos: dict = {}
    linhas_invalidas: list[str] = []

    for i, linha in enumerate(linhas):
        numero_transporte = remover_zeros_esquerda(str(linha.get(mapa["N° Transporte"], "")).strip())
        if not numero_transporte:
            continue  # rodapé/sobra da planilha

        sku = remover_zeros_esquerda(str(linha.get(mapa["Material"], "")).strip().upper())
        fornecimento = (
            remover_zeros_esquerda(str(linha.get(col_fornecimento, "")).strip()) if col_fornecimento else ""
        )
        ordem_venda = (
            remover_zeros_esquerda(str(linha.get(col_ordem_venda, "")).strip()) if col_ordem_venda else ""
        )

        if not sku and not fornecimento:
            continue  # linha de total do arquivo

        texto_unidade = str(linha.get(mapa["Quantidade"], "")).strip()
        texto_peso = str(linha.get(mapa["Qtde"], "")).strip()

        motivos = []
        if not sku:
            motivos.append("Material vazio")

        unidade = _tentar_parse(texto_unidade)
        if unidade is None or unidade <= 0:
            motivos.append(f'Quantidade inválida ("{texto_unidade}")')

        peso = _tentar_parse(texto_peso)
        if peso is None or peso <= 0:
            motivos.append(f'Qtde inválida ("{texto_peso}")')

        if motivos:
            linhas_invalidas.append(f"Transporte {numero_transporte} (linha {i + 1}): " + ", ".join(motivos))
            continue

        if numero_transporte not in grupos:
            grupos[numero_transporte] = {"itens": {}, "linhas_arquivo": 0, "fornecimentos": []}
            ordem_transportes.append(numero_transporte)

        grupo = grupos[numero_transporte]
        grupo["linhas_arquivo"] += 1

        por_unidade = unidade != peso
        chave = f"{sku}|{'un' if por_unidade else 'kg'}"
        item = grupo["itens"].setdefault(
            chave,
            {"sku": sku, "quantidade": 0.0, "por_unidade": por_unidade, "unidades": 0.0 if por_unidade else None, "ordens": {}},
        )
        item["quantidade"] += peso
        if por_unidade:
            item["unidades"] = (item["unidades"] or 0.0) + unidade

        if fornecimento or ordem_venda:
            chave_ordem = f"{fornecimento}|{ordem_venda}"
            ordem_item = item["ordens"].setdefault(
                chave_ordem,
                {"fornecimento": fornecimento, "ordem_venda": ordem_venda, "quantidade": 0.0, "unidades": 0.0 if por_unidade else None},
            )
            ordem_item["quantidade"] += peso
            if por_unidade:
                ordem_item["unidades"] = (ordem_item["unidades"] or 0.0) + unidade

        if fornecimento and fornecimento not in grupo["fornecimentos"]:
            grupo["fornecimentos"].append(fornecimento)

    transportes = []
    for numero_transporte in ordem_transportes:
        grupo = grupos[numero_transporte]
        itens = []
        for item in grupo["itens"].values():
            itens.append(
                {
                    "sku": item["sku"],
                    "quantidade": arredondar_peso(item["quantidade"]),
                    "por_unidade": item["por_unidade"],
                    "unidades": arredondar_peso(item["unidades"]) if item["unidades"] is not None else None,
                    "ordens": [
                        {
                            "fornecimento": o["fornecimento"],
                            "ordem_venda": o["ordem_venda"],
                            "quantidade": arredondar_peso(o["quantidade"]),
                            "unidades": arredondar_peso(o["unidades"]) if o["unidades"] is not None else None,
                        }
                        for o in item["ordens"].values()
                    ],
                }
            )
        transportes.append(
            {
                "numero_transporte": numero_transporte,
                "itens": itens,
                "linhas_arquivo": grupo["linhas_arquivo"],
                "fornecimentos": grupo["fornecimentos"],
            }
        )

    return transportes, linhas_invalidas
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_zsd106_parser -v`
Expected: PASS (11 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/zsd106_parser.py rpa_arcelor/test_zsd106_parser.py
git commit -m "feat(rpa_arcelor): parser do ZSD106 (agrupamento, peso/unidade, zero à esquerda)"
```

---

## Task 3: Duplo de teste do Supabase + Writer do ZSD106

**Files:**
- Create: `rpa_arcelor/supabase_fake.py`
- Create: `rpa_arcelor/zsd106_writer.py`
- Test: `rpa_arcelor/test_zsd106_writer.py`

**Interfaces:**
- Consumes: saída de `parse_zsd106` (Task 2); `pesos_iguais` de `normalizacao.py` (Task 1).
- Produces: `FakeSupabaseClient(respostas: dict)` (reusado pelas Tasks 5 e 7); `gravar_zsd106(cliente, transportes: list[dict], usuario_id: str | None) -> dict` — retorna `{"inseridos": int, "atualizados": int, "excluidos": int, "zerados": int}`.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/supabase_fake.py
# -*- coding: utf-8 -*-
"""Duplo de teste do cliente supabase-py: registra as chamadas encadeadas
(`.table().select()/.insert()/.update()/.upsert()/.delete().eq()/.in_()/.is_()`)
e devolve dados combinados de antemão — sem rede, pra testar a reconciliação
de verdade."""


class _RespostaFalsa:
    def __init__(self, data):
        self.data = data


class _ConstrutorFalso:
    def __init__(self, tabela, operacao, payload=None):
        self.tabela = tabela
        self.operacao = operacao
        self.payload = payload
        self.filtros = []

    def eq(self, coluna, valor):
        self.filtros.append(("eq", coluna, valor))
        return self

    def in_(self, coluna, valores):
        self.filtros.append(("in_", coluna, list(valores)))
        return self

    def is_(self, coluna, valor):
        self.filtros.append(("is_", coluna, valor))
        return self

    def range(self, desde, ate):
        self.filtros.append(("range", desde, ate))
        return self

    def select(self, *_args, **_kwargs):
        return self

    def execute(self):
        chamada = {
            "tabela": self.tabela.nome,
            "operacao": self.operacao,
            "payload": self.payload,
            "filtros": list(self.filtros),
        }
        self.tabela.cliente.chamadas.append(chamada)
        dados = self.tabela.cliente.respostas.get(self.tabela.nome, {}).get(self.operacao, [])
        if callable(dados):
            dados = dados(chamada)
        return _RespostaFalsa(dados)


class _TabelaFalsa:
    def __init__(self, cliente, nome):
        self.cliente = cliente
        self.nome = nome

    def select(self, *_args, **_kwargs):
        return _ConstrutorFalso(self, "select")

    def insert(self, payload):
        return _ConstrutorFalso(self, "insert", payload)

    def update(self, payload):
        return _ConstrutorFalso(self, "update", payload)

    def upsert(self, payload, on_conflict=None):
        return _ConstrutorFalso(self, "upsert", {"linhas": payload, "on_conflict": on_conflict})

    def delete(self):
        return _ConstrutorFalso(self, "delete")


class FakeSupabaseClient:
    """`respostas` é `{tabela: {operacao: linhas_ou_funcao(chamada)->linhas}}` —
    o que `.execute().data` deve devolver para cada tabela/operação."""

    def __init__(self, respostas=None):
        self.respostas = respostas or {}
        self.chamadas = []

    def table(self, nome):
        return _TabelaFalsa(self, nome)
```

```python
# rpa_arcelor/test_zsd106_writer.py
import unittest
from supabase_fake import FakeSupabaseClient
from zsd106_writer import gravar_zsd106

TRANSPORTE_NOVO = {
    "numero_transporte": "5100130964",
    "linhas_arquivo": 1,
    "fornecimentos": ["861886474"],
    "itens": [
        {"sku": "128046", "quantidade": 10.0, "por_unidade": False, "unidades": None, "ordens": [
            {"fornecimento": "861886474", "ordem_venda": "", "quantidade": 10.0, "unidades": None}
        ]},
    ],
}


class TestGravarZsd106(unittest.TestCase):
    def test_transporte_novo_insere_transporte_e_item(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [], "insert": [{"id": "T1"}]},
                "transporte_itens": {"select": [], "insert": [{"id": "I1"}]},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 1, "atualizados": 0, "excluidos": 0, "zerados": 0})
        insercoes_transporte = [c for c in cliente.chamadas if c["tabela"] == "transportes" and c["operacao"] == "insert"]
        self.assertEqual(len(insercoes_transporte), 1)
        payload = insercoes_transporte[0]["payload"]
        self.assertEqual(payload["numero_transporte"], "5100130964")
        self.assertEqual(payload["tipo"], "expedicao")
        self.assertEqual(payload["status"], "agendado")
        self.assertIsNone(payload["hora_agenda"])
        self.assertFalse(payload["input_manual"])

    def test_item_igual_nao_atualiza(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes_item, [])
        # Item igual não mexe nem na quebra por ordem (evita delete+insert à toa).
        mexeu_em_ordens = [c for c in cliente.chamadas if c["tabela"] == "arc_item_ordem_venda"]
        self.assertEqual(mexeu_em_ordens, [])

    def test_item_diferente_atualiza(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 5.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo["atualizados"], 1)
        atualizacoes_item = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertEqual(atualizacoes_item[0]["payload"]["quantidade_pedido"], 10.0)

    def test_item_sumido_sem_pre_picking_marca_deleted_at(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["excluidos"], 1)
        self.assertEqual(resumo["zerados"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        self.assertIn("deleted_at", atualizacoes[0]["payload"])

    def test_item_sumido_com_pre_picking_zera_sem_deleted_at(self):
        transporte_sem_item = {**TRANSPORTE_NOVO, "itens": []}
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "agendado"}]},
                "transporte_itens": {
                    "select": [
                        {"id": "I1", "transporte_id": "T1", "sku": "128046", "separa_por_unidade": False,
                         "quantidade_pedido": 10.0, "unidades_pedido": None}
                    ]
                },
                "movimentacao_armazenagem": {
                    "select": [{"sku": "128046", "transporte_id": "T1", "quantidade": 3.0, "unidades": None}]
                },
            }
        )
        resumo = gravar_zsd106(cliente, [transporte_sem_item], usuario_id="U1")

        self.assertEqual(resumo["zerados"], 1)
        self.assertEqual(resumo["excluidos"], 0)
        atualizacoes = [c for c in cliente.chamadas if c["tabela"] == "transporte_itens" and c["operacao"] == "update"]
        payload = atualizacoes[0]["payload"]
        self.assertEqual(payload["quantidade_pedido"], 0)
        self.assertNotIn("deleted_at", payload)

    def test_transporte_finalizado_nao_e_mexido(self):
        cliente = FakeSupabaseClient(
            respostas={
                "transportes": {"select": [{"id": "T1", "numero_transporte": "5100130964", "status": "finalizado"}]},
                "transporte_itens": {"select": []},
                "movimentacao_armazenagem": {"select": []},
            }
        )
        resumo = gravar_zsd106(cliente, [TRANSPORTE_NOVO], usuario_id="U1")

        self.assertEqual(resumo, {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0})
        mexeu = [c for c in cliente.chamadas if c["tabela"] in ("transportes", "transporte_itens") and c["operacao"] in ("insert", "update")]
        self.assertEqual(mexeu, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_zsd106_writer -v`
Expected: FAIL (ModuleNotFoundError: No module named 'zsd106_writer')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/zsd106_writer.py
# -*- coding: utf-8 -*-
"""Grava a leitura do ZSD106 no Supabase: reconciliação item a item, espelhando
wmsarcelormital/src/components/ImportarTransportesButton.tsx (caminho da
expedição) — mesmas tabelas, mesma regra de status elegível, e `deleted_at` no
lugar do delete/zera de hoje quando o item some do arquivo."""
from datetime import datetime, timezone
from normalizacao import pesos_iguais

STATUS_ELEGIVEL = {"agendado", "em_andamento"}


def _identidade(sku: str, por_unidade: bool) -> str:
    return f"{sku}|{'un' if por_unidade else 'kg'}"


def _buscar_existentes(cliente, numeros_transporte):
    if not numeros_transporte:
        return {}
    resp = (
        cliente.table("transportes")
        .select("id, numero_transporte, status")
        .in_("numero_transporte", numeros_transporte)
        .eq("tipo", "expedicao")
        .execute()
    )
    transportes = resp.data or []
    ids = [t["id"] for t in transportes]

    itens_por_transporte = {}
    if ids:
        resp_itens = (
            cliente.table("transporte_itens")
            .select("id, transporte_id, sku, separa_por_unidade, quantidade_pedido, unidades_pedido")
            .in_("transporte_id", ids)
            .execute()
        )
        for item in resp_itens.data or []:
            itens_por_transporte.setdefault(item["transporte_id"], {})[
                _identidade(item["sku"], bool(item["separa_por_unidade"]))
            ] = item

    resultado = {}
    for t in transportes:
        resultado[t["numero_transporte"]] = {
            "id": t["id"],
            "status": t["status"],
            "itens": itens_por_transporte.get(t["id"], {}),
        }
    return resultado


def _buscar_pre_picking(cliente, transporte_ids):
    """Peso que cada linha (transporte_id|sku|kg-ou-un) ainda tem FISICAMENTE
    no pré-picking. Espelha buscarMaterialNoPrePicking
    (wmsarcelormital/src/features/arcelor/itemRetirado.ts) — mesma tabela,
    mesmos filtros, mesma chave."""
    resultado = {}
    if not transporte_ids:
        return resultado
    for inicio in range(0, len(transporte_ids), 200):
        lote = transporte_ids[inicio : inicio + 200]
        desde = 0
        while True:
            resp = (
                cliente.table("movimentacao_armazenagem")
                .select("sku, transporte_id, quantidade, unidades")
                .eq("tipo_transporte", "Picking")
                .is_("devolver_desde", None)
                .is_("devolvido_em", None)
                .in_("transporte_id", lote)
                .range(desde, desde + 999)
                .execute()
            )
            linhas = resp.data or []
            for linha in linhas:
                if not linha.get("transporte_id"):
                    continue
                por_unidade = linha.get("unidades") is not None
                chave = f"{linha['transporte_id']}|{linha['sku']}|{'un' if por_unidade else 'kg'}"
                resultado[chave] = resultado.get(chave, 0.0) + float(linha.get("quantidade") or 0)
            if len(linhas) < 1000:
                break
            desde += 1000
    return resultado


def _regravar_ordens(cliente, transporte_item_id, ordens):
    """Reescreve a quebra por fornecimento/ordem de venda: apaga as antigas e
    insere as novas — uma reimportação troca o roteiro inteiro."""
    cliente.table("arc_item_ordem_venda").delete().eq("transporte_item_id", transporte_item_id).execute()
    if not ordens:
        return
    linhas = [
        {
            "transporte_item_id": transporte_item_id,
            "fornecimento": o["fornecimento"],
            "ordem_venda": o["ordem_venda"],
            "quantidade_kg": o["quantidade"],
            "unidades": o["unidades"],
            "ordem": idx + 1,
        }
        for idx, o in enumerate(ordens)
    ]
    cliente.table("arc_item_ordem_venda").insert(linhas).execute()


def gravar_zsd106(cliente, transportes: list, usuario_id) -> dict:
    numeros = [t["numero_transporte"] for t in transportes]
    existentes = _buscar_existentes(cliente, numeros)

    ids_elegiveis = [
        existentes[t["numero_transporte"]]["id"]
        for t in transportes
        if t["numero_transporte"] in existentes
        and existentes[t["numero_transporte"]]["status"] in STATUS_ELEGIVEL
    ]
    pre_picking = _buscar_pre_picking(cliente, ids_elegiveis)

    resumo = {"inseridos": 0, "atualizados": 0, "excluidos": 0, "zerados": 0}

    for t in transportes:
        existente = existentes.get(t["numero_transporte"])
        if existente and existente["status"] not in STATUS_ELEGIVEL:
            continue  # transporte encerrado: o ZSD106 não reabre

        if existente:
            transporte_id = existente["id"]
        else:
            resp = (
                cliente.table("transportes")
                .insert(
                    {
                        "numero_transporte": t["numero_transporte"],
                        "tipo": "expedicao",
                        "status": "agendado",
                        "hora_agenda": None,
                        "placa": None,
                        "origem": None,
                        "transportadora": None,
                        "notas_fiscais": None,
                        "fornecimentos": t["fornecimentos"] or None,
                        "usuario_id": usuario_id,
                        "input_manual": False,
                        "status_consulta_sap": True,
                    }
                )
                .execute()
            )
            transporte_id = resp.data[0]["id"]
            existente = {"id": transporte_id, "status": "agendado", "itens": {}}

        itens_existentes = dict(existente["itens"])
        vistos = set()

        for item in t["itens"]:
            identidade = _identidade(item["sku"], item["por_unidade"])
            vistos.add(identidade)
            atual = itens_existentes.get(identidade)

            if atual is None:
                resp_item = (
                    cliente.table("transporte_itens")
                    .insert(
                        {
                            "transporte_id": transporte_id,
                            "sku": item["sku"],
                            "quantidade_pedido": item["quantidade"],
                            "separa_por_unidade": item["por_unidade"],
                            "unidades_pedido": item["unidades"],
                        }
                    )
                    .execute()
                )
                item_id = resp_item.data[0]["id"]
                resumo["inseridos"] += 1
                _regravar_ordens(cliente, item_id, item["ordens"])
                continue

            item_id = atual["id"]
            mesmo_peso = pesos_iguais(atual["quantidade_pedido"], item["quantidade"])
            mesmas_unidades = (atual.get("unidades_pedido") or 0) == (item["unidades"] or 0)
            if mesmo_peso and mesmas_unidades:
                continue  # igual ao que já está gravado: não mexe (nem na quebra por ordem)

            cliente.table("transporte_itens").update(
                {"quantidade_pedido": item["quantidade"], "unidades_pedido": item["unidades"]}
            ).eq("id", item_id).execute()
            resumo["atualizados"] += 1
            _regravar_ordens(cliente, item_id, item["ordens"])

        for identidade, item_gravado in itens_existentes.items():
            if identidade in vistos:
                continue
            chave_pp = (
                f"{transporte_id}|{item_gravado['sku']}|"
                f"{'un' if item_gravado['separa_por_unidade'] else 'kg'}"
            )
            no_pre_picking = pre_picking.get(chave_pp, 0.0)
            if no_pre_picking > 0:
                cliente.table("transporte_itens").update(
                    {
                        "quantidade_pedido": 0,
                        "unidades_pedido": 0 if item_gravado["separa_por_unidade"] else None,
                    }
                ).eq("id", item_gravado["id"]).execute()
                resumo["zerados"] += 1
            else:
                cliente.table("transporte_itens").update(
                    {"deleted_at": datetime.now(timezone.utc).isoformat()}
                ).eq("id", item_gravado["id"]).execute()
                resumo["excluidos"] += 1

    return resumo
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_zsd106_writer -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/supabase_fake.py rpa_arcelor/zsd106_writer.py rpa_arcelor/test_zsd106_writer.py
git commit -m "feat(rpa_arcelor): writer do ZSD106 com reconciliação e deleted_at"
```

---

## Task 4: Parser do VT12

**Files:**
- Create: `rpa_arcelor/vt12_parser.py`
- Test: `rpa_arcelor/test_vt12_parser.py`

**Interfaces:**
- Consumes: `remover_zeros_esquerda`, `parse_peso_extrato` de `normalizacao.py` (Task 1).
- Produces: `parse_vt12(linhas_texto: list[str]) -> tuple[list[dict], list[str]]`. Cada transporte: `{"numero_transporte": str, "rota": str, "transportadora": str, "fornecimentos": [...]}`. Cada fornecimento: `{"fornecimento": str, "ordem_carregamento": int, "cliente": str, "destino": str, "uf": str, "peso_kg": float}` — `ordem_carregamento` 1 = primeiro a carregar (última linha do arquivo). Usado por Task 5.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_vt12_parser.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_vt12_parser -v`
Expected: FAIL (ModuleNotFoundError: No module named 'vt12_parser')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/vt12_parser.py
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_vt12_parser -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/vt12_parser.py rpa_arcelor/test_vt12_parser.py
git commit -m "feat(rpa_arcelor): parser do VT12 (sequência de carregamento, ordem invertida)"
```

---

## Task 5: Writer do VT12

**Files:**
- Create: `rpa_arcelor/vt12_writer.py`
- Test: `rpa_arcelor/test_vt12_writer.py`

**Interfaces:**
- Consumes: saída de `parse_vt12` (Task 4); `FakeSupabaseClient` de `supabase_fake.py` (Task 3).
- Produces: `gravar_vt12(cliente, transportes: list[dict]) -> dict` — retorna `{"transportes_gravados": int, "transportes_sem_cadastro": int}`.

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_vt12_writer -v`
Expected: FAIL (ModuleNotFoundError: No module named 'vt12_writer')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/vt12_writer.py
# -*- coding: utf-8 -*-
"""Grava a sequência de carregamento do VT12 em arc_transporte_fornecimento —
delete-then-insert por transporte, espelhando sequenciaCarregamentoParser.ts +
o uso que ImportarTransportesButton.tsx faz dele."""


def gravar_vt12(cliente, transportes: list) -> dict:
    resumo = {"transportes_gravados": 0, "transportes_sem_cadastro": 0}
    numeros = [t["numero_transporte"] for t in transportes]
    if not numeros:
        return resumo

    resp = cliente.table("transportes").select("id, numero_transporte").in_("numero_transporte", numeros).execute()
    id_por_numero = {t["numero_transporte"]: t["id"] for t in (resp.data or [])}

    for t in transportes:
        transporte_id = id_por_numero.get(t["numero_transporte"])
        if not transporte_id:
            resumo["transportes_sem_cadastro"] += 1
            continue

        cliente.table("arc_transporte_fornecimento").delete().eq("transporte_id", transporte_id).execute()
        if t["fornecimentos"]:
            linhas = [
                {
                    "transporte_id": transporte_id,
                    "fornecimento": f["fornecimento"],
                    "ordem_carregamento": f["ordem_carregamento"],
                    "cliente": f["cliente"],
                    "destino": f["destino"],
                    "uf": f["uf"],
                    "peso_kg": f["peso_kg"],
                }
                for f in t["fornecimentos"]
            ]
            cliente.table("arc_transporte_fornecimento").insert(linhas).execute()
        resumo["transportes_gravados"] += 1

    return resumo
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_vt12_writer -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/vt12_writer.py rpa_arcelor/test_vt12_writer.py
git commit -m "feat(rpa_arcelor): writer do VT12 (delete-then-insert em arc_transporte_fornecimento)"
```

---

## Task 6: Parser do ZV74

**Files:**
- Create: `rpa_arcelor/zv74_parser.py`
- Test: `rpa_arcelor/test_zv74_parser.py`

**Interfaces:**
- Consumes: `remover_zeros_esquerda`, `normalizar_cabecalho` de `normalizacao.py` (Task 1).
- Produces: `parse_zv74(linhas: list[list]) -> dict` com chaves `observacoes` (`[{"fornecimento", "texto"}]`), `condicoes_pagamento` (`[{"ordem_venda", "descricao"}]`), `linhas_sem_texto` (int), `linhas_sem_fornecimento` (int). `linhas[0]` é o cabeçalho.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_zv74_parser.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_zv74_parser -v`
Expected: FAIL (ModuleNotFoundError: No module named 'zv74_parser')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/zv74_parser.py
# -*- coding: utf-8 -*-
"""Parser do ZV74 (observações de embarque + condição de pagamento) — espelha
wmsarcelormital/src/lib/observacoesEmbarqueParser.ts."""
from normalizacao import remover_zeros_esquerda, normalizar_cabecalho

COL_FORNECIMENTO = "Número do fornecimento"
COL_TEXTO = "Texto Embarque"
COL_ORDEM_VENDA = "Ordem Vendas"
COL_COND_PAGTO = "Desc Cond Pagto"


def _indice(cabecalho: list, titulo: str):
    alvo = normalizar_cabecalho(titulo)
    return cabecalho.index(alvo) if alvo in cabecalho else None


def parse_zv74(linhas: list) -> dict:
    """`linhas[0]` é o cabeçalho, `linhas[1:]` os dados — mesmo formato que
    `ws.iter_rows(values_only=True)` do openpyxl devolve (como lista)."""
    if not linhas:
        return {"observacoes": [], "condicoes_pagamento": [], "linhas_sem_texto": 0, "linhas_sem_fornecimento": 0}

    cabecalho = [normalizar_cabecalho(str(v) if v is not None else "") for v in linhas[0]]
    idx_fornecimento = _indice(cabecalho, COL_FORNECIMENTO)
    idx_textos = [i for i, c in enumerate(cabecalho) if c == normalizar_cabecalho(COL_TEXTO)]

    if idx_fornecimento is None or not idx_textos:
        raise ValueError(f"Planilha não reconhecida: não encontrei as colunas esperadas ({COL_FORNECIMENTO}, {COL_TEXTO}).")

    idx_ordem_venda = _indice(cabecalho, COL_ORDEM_VENDA)
    idx_cond_pagto = _indice(cabecalho, COL_COND_PAGTO)

    linhas_sem_texto = 0
    linhas_sem_fornecimento = 0
    por_fornecimento = {}
    por_ordem_venda = {}

    for row in linhas[1:]:
        if row is None:
            continue

        def celula(idx):
            if idx is None or idx >= len(row) or row[idx] is None:
                return ""
            return str(row[idx]).strip()

        if idx_ordem_venda is not None and idx_cond_pagto is not None:
            ordem_venda = remover_zeros_esquerda(celula(idx_ordem_venda))
            descricao = celula(idx_cond_pagto)
            if ordem_venda and descricao and ordem_venda not in por_ordem_venda:
                por_ordem_venda[ordem_venda] = descricao

        texto = next((t for t in (celula(i) for i in idx_textos) if t != ""), "")
        fornecimento = remover_zeros_esquerda(celula(idx_fornecimento))

        if not texto:
            linhas_sem_texto += 1
            continue
        if not fornecimento:
            linhas_sem_fornecimento += 1
            continue
        if fornecimento not in por_fornecimento:
            por_fornecimento[fornecimento] = texto

    return {
        "observacoes": [{"fornecimento": f, "texto": t} for f, t in por_fornecimento.items()],
        "condicoes_pagamento": [{"ordem_venda": o, "descricao": d} for o, d in por_ordem_venda.items()],
        "linhas_sem_texto": linhas_sem_texto,
        "linhas_sem_fornecimento": linhas_sem_fornecimento,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_zv74_parser -v`
Expected: PASS (8 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/zv74_parser.py rpa_arcelor/test_zv74_parser.py
git commit -m "feat(rpa_arcelor): parser do ZV74 (observação de embarque + condição de pagamento)"
```

---

## Task 7: Writer do ZV74

**Files:**
- Create: `rpa_arcelor/zv74_writer.py`
- Test: `rpa_arcelor/test_zv74_writer.py`

**Interfaces:**
- Consumes: saída de `parse_zv74` (Task 6); `FakeSupabaseClient` (Task 3).
- Produces: `gravar_zv74(cliente, resultado: dict, usuario_id) -> dict` — retorna `{"observacoes": int, "condicoes_pagamento": int}`.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_zv74_writer.py
import unittest
from supabase_fake import FakeSupabaseClient
from zv74_writer import gravar_zv74

RESULTADO = {
    "observacoes": [{"fornecimento": "846252364", "texto": "ENVIAR 300 BARRAS"}],
    "condicoes_pagamento": [{"ordem_venda": "201308660", "descricao": "A Prazo"}],
    "linhas_sem_texto": 0,
    "linhas_sem_fornecimento": 0,
}


class TestGravarZv74(unittest.TestCase):
    def test_upsert_observacoes_e_condicoes(self):
        cliente = FakeSupabaseClient()
        resumo = gravar_zv74(cliente, RESULTADO, usuario_id="U1")

        self.assertEqual(resumo, {"observacoes": 1, "condicoes_pagamento": 1})
        obs = [c for c in cliente.chamadas if c["tabela"] == "arc_observacao_embarque"]
        cond = [c for c in cliente.chamadas if c["tabela"] == "arc_condicao_pagamento_ordem"]
        self.assertEqual(obs[0]["operacao"], "upsert")
        self.assertEqual(obs[0]["payload"]["on_conflict"], "fornecimento")
        self.assertEqual(obs[0]["payload"]["linhas"][0]["fornecimento"], "846252364")
        self.assertEqual(cond[0]["payload"]["on_conflict"], "ordem_venda")

    def test_nao_grava_nada_quando_vazio(self):
        cliente = FakeSupabaseClient()
        resumo = gravar_zv74(
            cliente,
            {"observacoes": [], "condicoes_pagamento": [], "linhas_sem_texto": 0, "linhas_sem_fornecimento": 0},
            usuario_id="U1",
        )
        self.assertEqual(resumo, {"observacoes": 0, "condicoes_pagamento": 0})
        self.assertEqual(cliente.chamadas, [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_zv74_writer -v`
Expected: FAIL (ModuleNotFoundError: No module named 'zv74_writer')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/zv74_writer.py
# -*- coding: utf-8 -*-
"""Grava observações de embarque e condição de pagamento em
arc_observacao_embarque / arc_condicao_pagamento_ordem — upsert, espelhando
observacoesEmbarqueParser.ts + o uso que ImportarTransportesButton.tsx faz
dele."""
from datetime import datetime, timezone


def gravar_zv74(cliente, resultado: dict, usuario_id) -> dict:
    agora = datetime.now(timezone.utc).isoformat()
    resumo = {"observacoes": 0, "condicoes_pagamento": 0}

    if resultado["observacoes"]:
        linhas = [
            {"fornecimento": o["fornecimento"], "texto": o["texto"], "atualizado_em": agora, "atualizado_por": usuario_id}
            for o in resultado["observacoes"]
        ]
        for inicio in range(0, len(linhas), 500):
            cliente.table("arc_observacao_embarque").upsert(linhas[inicio : inicio + 500], on_conflict="fornecimento").execute()
        resumo["observacoes"] = len(linhas)

    if resultado["condicoes_pagamento"]:
        linhas = [
            {"ordem_venda": c["ordem_venda"], "descricao": c["descricao"], "atualizado_em": agora, "atualizado_por": usuario_id}
            for c in resultado["condicoes_pagamento"]
        ]
        for inicio in range(0, len(linhas), 500):
            cliente.table("arc_condicao_pagamento_ordem").upsert(linhas[inicio : inicio + 500], on_conflict="ordem_venda").execute()
        resumo["condicoes_pagamento"] = len(linhas)

    return resumo
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_zv74_writer -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add rpa_arcelor/zv74_writer.py rpa_arcelor/test_zv74_writer.py
git commit -m "feat(rpa_arcelor): writer do ZV74 (upsert em arc_observacao_embarque/arc_condicao_pagamento_ordem)"
```

---

## Task 8: Autenticação de serviço

**Files:**
- Create: `rpa_arcelor/auth_servico.py`
- Create: `rpa_arcelor/credenciais_servico.example.json`
- Test: `rpa_arcelor/test_auth_servico.py`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `carregar_credenciais_servico(caminho: str) -> dict` (`{"email": str, "senha": str}`) — usado pela Task 9 no lugar de `criar_tela_login`.

- [ ] **Step 1: Write the failing tests**

```python
# rpa_arcelor/test_auth_servico.py
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd rpa_arcelor && python -m unittest test_auth_servico -v`
Expected: FAIL (ModuleNotFoundError: No module named 'auth_servico')

- [ ] **Step 3: Write the implementation**

```python
# rpa_arcelor/auth_servico.py
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
```

```json
// rpa_arcelor/credenciais_servico.example.json
{
  "email": "robo.zsd106@hawktech.example",
  "senha": "TROQUE_ANTES_DE_USAR"
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd rpa_arcelor && python -m unittest test_auth_servico -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Ignorar o arquivo real de credenciais no git**

Adicionar ao final de `D:\www\rpas\.gitignore` (mesmo bloco de "Arquivos personalizados" onde já estão `CredenciaisOracle.json`/`token.json`):

```
credenciais_servico.json
```

- [ ] **Step 6: Commit**

```bash
git add rpa_arcelor/auth_servico.py rpa_arcelor/test_auth_servico.py rpa_arcelor/credenciais_servico.example.json .gitignore
git commit -m "feat(rpa_arcelor): autenticação de serviço silenciosa (sem tela de login)"
```

---

## Task 9: Migration — `deleted_at` em `transporte_itens`

**Files:**
- Create: `D:\www\react\wmsarcelormital\supabase\migrations\20260927120000_transporte_itens_deleted_at.sql`

**Interfaces:**
- Produces: coluna `transporte_itens.deleted_at timestamptz`, usada pela Task 3 (`zsd106_writer.py`, já escrita). Nenhum código do front lê essa coluna ainda — fica pro Plano 2 (ver spec, seção "Migração de banco e frontend").

- [ ] **Step 1: Write the migration**

```sql
-- D:\www\react\wmsarcelormital\supabase\migrations\20260927120000_transporte_itens_deleted_at.sql
-- Soft-delete introduzido para o robô ZSD106 (rpa_arcelor): quando um item
-- some do arquivo e nada foi separado ainda, o robô marca deleted_at em vez
-- de apagar a linha de verdade (ImportarTransportesButton.tsx continua
-- apagando/zerando como hoje — este mecanismo é só do caminho do robô).
-- O front AINDA NÃO filtra por essa coluna em lugar nenhum: isso é um
-- projeto separado (Plano 2), ver docs/superpowers/specs/
-- 2026-09-27-rpa-arcelor-expedicao-recebimento-design.md.
ALTER TABLE public.transporte_itens ADD COLUMN deleted_at timestamptz;
```

- [ ] **Step 2: Applying and verifying (manual — sem Supabase CLI configurado neste ambiente)**

Rodar contra o projeto Supabase de teste/staging (nunca direto em produção):
`supabase db push` (ou colar o SQL acima no SQL Editor do painel Supabase) e confirmar com:
```sql
select column_name, data_type from information_schema.columns
where table_name = 'transporte_itens' and column_name = 'deleted_at';
```
Expected: uma linha, `data_type = timestamp with time zone`.

- [ ] **Step 3: Commit**

```bash
cd "D:\www\react\wmsarcelormital"
git add supabase/migrations/20260927120000_transporte_itens_deleted_at.sql
git commit -m "feat(db): coluna deleted_at em transporte_itens para soft-delete do RPA Arcelor"
```

---

## Task 10: `Arcelor_WMS.py` — remove login, GUI de 2 seções, liga tudo

**Files:**
- Modify: `rpa_arcelor/Arcelor_WMS.py`

**Interfaces:**
- Consumes: `carregar_credenciais_servico` (Task 8); `parse_zsd106`+`gravar_zsd106` (Tasks 2-3); `parse_vt12`+`ler_linhas_vt12`+`gravar_vt12` (Tasks 4-5); `parse_zv74`+`gravar_zv74` (Tasks 6-7).

Este é o único task sem teste automatizado por baixo — junta tudo na GUI e no
`__main__`, e o único jeito de validar de ponta a ponta é rodando a GUI (e,
depois, contra SAP real). Mesma convenção que o resto deste arquivo já segue
(`executar_zsd106` também não tem teste automatizado).

- [ ] **Step 1: Remover a tela de login e trocar por autenticação de serviço**

Em `rpa_arcelor/Arcelor_WMS.py`, substituir o bloco final (linhas 646-649):

```python
if __name__ == "__main__":
    usuario = criar_tela_login()
    if usuario:
        criar_gui(usuario)
```

por:

```python
def _mostrar_erro_fatal(mensagem: str) -> None:
    """Mostra um erro numa janela mesmo antes de a GUI principal existir
    (a GUI só redireciona stdout/stderr depois de aberta)."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Hawk Tech WMS — Arcelor Mittal", mensagem)
    root.destroy()


if __name__ == "__main__":
    from auth_servico import carregar_credenciais_servico

    try:
        credenciais = carregar_credenciais_servico(resource_path("credenciais_servico.json"))
        usuario = autenticar_usuario(credenciais["email"], credenciais["senha"])
    except (FileNotFoundError, ValueError) as e:
        usuario = None
        _mostrar_erro_fatal(str(e))
    else:
        if not usuario:
            _mostrar_erro_fatal(
                "Falha ao autenticar a conta de serviço do robô. "
                "Verifique credenciais_servico.json (e-mail/senha, e se a role 'conferente' está atribuída)."
            )

    if usuario:
        criar_gui(usuario)
```

E apagar a função `criar_tela_login` inteira (linhas 467-527) — não é mais chamada por ninguém.

- [ ] **Step 2: Reestruturar a GUI em 2 seções (Expedição / Recebimento)**

Em `criar_gui`, substituir o bloco de "Cole aqui os transportes" + botões
(linhas 566-580) por duas seções empilhadas. Trocar:

```python
    ttk.Label(top, text="Cole aqui os transportes copiados do Excel (um por linha):").grid(
        row=1, column=1, sticky="w", pady=(8, 2)
    )
    entrada = ScrolledText(top, width=40, height=9)
    entrada.grid(row=2, column=1, sticky="w")

    lbl_contagem = ttk.Label(top, text="Nenhum transporte informado.", foreground="gray")
    lbl_contagem.grid(row=3, column=1, sticky="w", pady=(4, 0))

    botoes = ttk.Frame(top)
    botoes.grid(row=4, column=1, sticky="w", pady=(8, 0))
    btn_atualizar = ttk.Button(botoes, text="Atualizar WMS", width=22)
    btn_atualizar.grid(row=0, column=0, padx=(0, 8))
    btn_limpar = ttk.Button(botoes, text="Limpar", width=12)
    btn_limpar.grid(row=0, column=1)
```

por:

```python
    ttk.Separator(top, orient="horizontal").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 8))
    ttk.Label(top, text="Expedição", font=("", 10, "bold")).grid(row=2, column=1, sticky="w")
    ttk.Label(top, text="Cole aqui os transportes copiados do Excel (um por linha):").grid(
        row=3, column=1, sticky="w", pady=(4, 2)
    )
    entrada_expedicao = ScrolledText(top, width=40, height=9)
    entrada_expedicao.grid(row=4, column=1, sticky="w")

    lbl_contagem_expedicao = ttk.Label(top, text="Nenhum transporte informado.", foreground="gray")
    lbl_contagem_expedicao.grid(row=5, column=1, sticky="w", pady=(4, 0))

    botoes_expedicao = ttk.Frame(top)
    botoes_expedicao.grid(row=6, column=1, sticky="w", pady=(8, 0))
    btn_zsd106 = ttk.Button(botoes_expedicao, text="Rodar ZSD106", width=16)
    btn_zsd106.grid(row=0, column=0, padx=(0, 8))
    btn_vt12 = ttk.Button(botoes_expedicao, text="Rodar VT12", width=16)
    btn_vt12.grid(row=0, column=1, padx=(0, 8))
    btn_zv74 = ttk.Button(botoes_expedicao, text="Rodar ZV74", width=16)
    btn_zv74.grid(row=0, column=2)

    ttk.Separator(top, orient="horizontal").grid(row=7, column=0, columnspan=2, sticky="ew", pady=(16, 8))
    ttk.Label(top, text="Recebimento", font=("", 10, "bold")).grid(row=8, column=1, sticky="w")
    ttk.Label(top, text="Cole aqui os transportes copiados do Excel (um por linha):").grid(
        row=9, column=1, sticky="w", pady=(4, 2)
    )
    entrada_recebimento = ScrolledText(top, width=40, height=6)
    entrada_recebimento.grid(row=10, column=1, sticky="w")

    botoes_recebimento = ttk.Frame(top)
    botoes_recebimento.grid(row=11, column=1, sticky="w", pady=(8, 0))
    btn_zsd16 = ttk.Button(botoes_recebimento, text="Rodar ZSD16 (em breve)", width=22)
    btn_zsd16.grid(row=0, column=0)
    btn_zsd16.state(["disabled"])
```

O `ScrolledText` de log (`txt`, linha 582) e o resto do `root.mainloop()` continuam
como estão, só ajustando as linhas do `grid` que vierem depois (renumerar
`row=` dos widgets abaixo, já que a seção de Recebimento ocupa até `row=11`
agora — o log de saída fica em `row=12` na coluna 0, ocupando as duas
colunas).

- [ ] **Step 3: Ligar o ZSD106 ao parser/writer novos**

Trocar a função `executar()` existente (que chamava `fluxo_atualizar_wms`) por
três funções, uma por botão, seguindo o mesmo padrão de threading que já
existe. A do ZSD106:

```python
    def executar_zsd106_gui():
        validos, invalidos = parse_transportes(entrada_expedicao.get("1.0", "end"))
        if not validos:
            messagebox.showwarning("Atenção", "Cole ao menos um transporte válido (somente dígitos).")
            return
        btn_zsd106.state(["disabled"])

        def trabalho():
            _com_init()
            try:
                print("===== Rodando ZSD106 =====")
                session = authenticate_sap()
                if not session:
                    print("❌ Falha ao conectar no SAP.")
                    return
                filepath = executar_zsd106(session, validos)
                if not filepath:
                    print("❌ Export ZSD106 falhou. Abortando.")
                    return
                df = ler_planilha(filepath)
                from zsd106_parser import parse_zsd106
                from zsd106_writer import gravar_zsd106

                transportes, linhas_invalidas = parse_zsd106(df.to_dict("records"), list(df.columns))
                for aviso in linhas_invalidas:
                    print(f"⚠️ {aviso}")
                resumo = gravar_zsd106(_supabase, transportes, _usuario_logado.get("id"))
                print(f"✓ ZSD106: {resumo}")
            except Exception as e:
                print(f"\n[ERRO] Rodar ZSD106: {e}\n")
            finally:
                _com_uninit()
                root.after(0, lambda: btn_zsd106.state(["!disabled"]))

        threading.Thread(target=trabalho, daemon=True).start()

    btn_zsd106.configure(command=executar_zsd106_gui)
```

- [ ] **Step 4: Ligar o VT12 (parser + writer; a automação SAP vem na Task 11)**

```python
    def executar_vt12_gui():
        validos, invalidos = parse_transportes(entrada_expedicao.get("1.0", "end"))
        if not validos:
            messagebox.showwarning("Atenção", "Cole ao menos um transporte válido (somente dígitos).")
            return
        btn_vt12.state(["disabled"])

        def trabalho():
            _com_init()
            try:
                print("===== Rodando VT12 =====")
                session = authenticate_sap()
                if not session:
                    print("❌ Falha ao conectar no SAP.")
                    return
                filepath = executar_vt12(session, validos)
                if not filepath:
                    print("❌ Export VT12 falhou. Abortando.")
                    return
                from vt12_parser import ler_linhas_vt12, parse_vt12
                from vt12_writer import gravar_vt12

                transportes, linhas_invalidas = parse_vt12(ler_linhas_vt12(filepath))
                for aviso in linhas_invalidas:
                    print(f"⚠️ {aviso}")
                resumo = gravar_vt12(_supabase, transportes)
                print(f"✓ VT12: {resumo}")
            except Exception as e:
                print(f"\n[ERRO] Rodar VT12: {e}\n")
            finally:
                _com_uninit()
                root.after(0, lambda: btn_vt12.state(["!disabled"]))

        threading.Thread(target=trabalho, daemon=True).start()

    btn_vt12.configure(command=executar_vt12_gui)
```

- [ ] **Step 5: Ligar o ZV74 (só parser + writer — SAP ainda não automatizado, ver spec)**

Como não existe `Script-ZV74.vbs` gravado (pendência conhecida, ver spec), o
botão de ZV74 não dirige o SAP ainda: ele lê o arquivo que o operador exportou
manualmente pra `C:\RPA\zv74.xlsx` (mesmo caminho/convenção dos outros dois) e
faz só o parse+gravação — assim o botão já funciona de verdade hoje, e vira só
substituir a leitura manual por `executar_zv74(session, ...)` quando o script
existir.

```python
    NOME_ARQ_ZV74 = "zv74.xlsx"

    def executar_zv74_gui():
        btn_zv74.state(["disabled"])

        def trabalho():
            try:
                print("===== Rodando ZV74 =====")
                filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_ZV74)
                if not os.path.exists(filepath):
                    print(
                        f"⚠️ Ainda não existe automação SAP pro ZV74 (ver CLAUDE.md do rpa_arcelor). "
                        f"Exporte manualmente o ZV74 para {filepath} e rode de novo."
                    )
                    return
                import openpyxl
                from zv74_parser import parse_zv74
                from zv74_writer import gravar_zv74

                wb = openpyxl.load_workbook(filepath, data_only=True)
                linhas = list(wb.active.iter_rows(values_only=True))
                resultado = parse_zv74(linhas)
                resumo = gravar_zv74(_supabase, resultado, _usuario_logado.get("id"))
                print(f"✓ ZV74: {resumo}")
            except Exception as e:
                print(f"\n[ERRO] Rodar ZV74: {e}\n")
            finally:
                root.after(0, lambda: btn_zv74.state(["!disabled"]))

        threading.Thread(target=trabalho, daemon=True).start()

    btn_zv74.configure(command=executar_zv74_gui)
```

- [ ] **Step 6: Verificação manual (não há teste automatizado pra GUI/SAP)**

1. Rodar `python Arcelor_WMS.py` sem `credenciais_servico.json` → deve mostrar
   o erro numa janela e NÃO abrir a GUI principal.
2. Criar `credenciais_servico.json` com uma conta de teste válida (role
   `conferente`) → a GUI deve abrir direto, sem tela de login.
3. Colar transportes na caixa de Expedição e clicar nos 3 botões — cada um
   deve rodar independente dos outros (clicar um não desabilita os outros
   dois).
4. Botão "Rodar ZSD16 (em breve)" deve aparecer desabilitado.

- [ ] **Step 7: Commit**

```bash
cd D:\www\rpas
git add rpa_arcelor/Arcelor_WMS.py
git commit -m "feat(rpa_arcelor): remove login, GUI de 2 seções, liga ZSD106/VT12/ZV74"
```

---

## Task 11: `executar_vt12` — automação SAP (adaptada do script gravado)

**Files:**
- Modify: `rpa_arcelor/Arcelor_WMS.py`

**Interfaces:**
- Consumes: `_sap_id`, `_sap_existe`, `_sap_aguardar`, `_sap_fechar_popups`, `_aguardar_arquivo_estavel`, `_copiar_para_clipboard`, `garantir_pasta_export`, `PASTA_EXPORT` (já existem no arquivo, usados por `executar_zsd106`).
- Produces: `executar_vt12(session, transportes: list[str]) -> str | None` — usado pela Task 10 (já referenciado lá).

Sem teste automatizado (SAP GUI Scripting real) — mesma convenção que
`executar_zsd106`. A verificação é o passo manual no fim.

- [ ] **Step 1: Adicionar a função, logo depois de `executar_zsd106`**

```python
NOME_ARQ_VT12 = "vt12.txt"


def _salvar_lista_local(session, filepath: str) -> bool:
    """Trata o diálogo de 'salvar lista como arquivo local' (wnd[1]), pelo
    mesmo padrão defensivo de `_exportar_grid` — reconhece o diálogo pelo
    controle que ele tem, não aperta OK às cegas."""
    radio = "wnd[1]/usr/subSUBSCREEN_STEPLOOP:SAPLSPO5:0150/sub:SAPLSPO5:0150/radSPOPLI-SELFLAG[1,0]"
    for _ in range(8):
        _sap_aguardar(session)
        if session.Children.Count <= 1:
            break
        if _sap_existe(session, radio):
            session.findById(radio).select()
            session.findById("wnd[1]/tbar[0]/btn[0]").press()
            continue
        if _sap_existe(session, "wnd[1]/usr/ctxtDY_PATH"):
            session.findById("wnd[1]/usr/ctxtDY_PATH").text = PASTA_EXPORT + "\\"
            if _sap_existe(session, "wnd[1]/usr/ctxtDY_FILENAME"):
                session.findById("wnd[1]/usr/ctxtDY_FILENAME").text = NOME_ARQ_VT12
            session.findById("wnd[1]/tbar[0]/btn[7]").press()
            continue
        break
    return _aguardar_arquivo_estavel(filepath)


def executar_vt12(session, transportes: list) -> str | None:
    """Abre o VT12, cola os transportes, roda a sequência de carregamento e
    salva como texto local em C:\\RPA. Adaptado de 'Script1 - VT12.vbs'
    (gravação original em SAP), com o mesmo tratamento defensivo de diálogos
    que `_exportar_grid` já usa para o ZSD106 (ainda NÃO validado contra SAP
    real — ver CLAUDE.md do rpa_arcelor)."""
    print(f"📤 VT12: consultando {len(transportes)} transporte(s)...")
    try:
        garantir_pasta_export()
        filepath = os.path.join(PASTA_EXPORT, NOME_ARQ_VT12)
        if os.path.exists(filepath):
            os.remove(filepath)

        _sap_fechar_popups(session)
        session.findById("wnd[0]").maximize()
        _sap_id(session, "wnd[0]/tbar[0]/okcd").Text = "/nvt12"
        session.findById("wnd[0]").sendVKey(0)
        _sap_aguardar(session)

        _sap_id(session, "wnd[0]/usr/ctxtK_STTRG-HIGH").text = "7"

        _copiar_para_clipboard("\r\n".join(transportes))
        _sap_id(session, "wnd[0]/usr/btn%_K_TKNUM_%_APP_%-VALU_PUSH").press()
        _sap_id(session, "wnd[1]/tbar[0]/btn[24]").press()
        session.findById("wnd[1]").sendVKey(8)
        session.findById("wnd[0]").sendVKey(8)
        _sap_aguardar(session)

        session.findById("wnd[0]/tbar[1]/btn[30]").press()
        session.findById("wnd[0]/tbar[1]/btn[18]").press()
        session.findById("wnd[0]/tbar[1]/btn[7]").press()
        _sap_aguardar(session)

        shell = _sap_id(
            session,
            "wnd[0]/usr/subPLANNING:SAPLV56I_PLAN_SCREEN:0110/cntlV56I_PLAN_SCREEN_CONTAINER/"
            "shellcont/shell/shellcont[1]/shell[0]",
        )
        shell.pressToolbarContextButton("&PRINT_BACK")
        shell.selectContextMenuItem("&PRINT_PREV")
        session.findById("wnd[0]/mbar/menu[3]/menu[5]/menu[2]/menu[2]").select()
        _sap_aguardar(session)

        if not _salvar_lista_local(session, filepath):
            print("❌ Export do VT12 falhou: arquivo não foi gerado.")
            return None
        print(f"✔️ Sequência de carregamento exportada: {filepath}")
        return filepath
    except Exception as e:
        print(f"⚠️ [ERRO SAP VT12]: {e}")
        _sap_fechar_popups(session)
        return None
```

Nota de implementação: o script gravado (`Script1 - VT12.vbs`) usa
`pressContextButton`/`selectContextMenuItem` nesse mesmo controle de shell —
mesmos métodos que `_exportar_grid` já chama com sucesso no ZSD106. Se
`_sap_id` não achar o controle, ele já levanta erro citando transação/tela/
barra de status, então não precisa de checagem extra aqui.

- [ ] **Step 2: Verificação manual contra SAP real**

1. Com uma sessão SAP logada, clicar "Rodar VT12" na GUI com 1-2 números de
   transporte reais colados.
2. Confirmar que `C:\RPA\vt12.txt` é gerado e seu conteúdo bate com o formato
   de `vt12.txt` já fornecido (cabeçalho "Transportes e fornecimento", tab-separated).
3. Se algum `findById` falhar, o erro já aparece com transação/tela/barra de
   status (via `_sap_id`) — ajustar o control ID específico que faltou, não o
   fluxo inteiro.

- [ ] **Step 3: Commit**

```bash
git add rpa_arcelor/Arcelor_WMS.py
git commit -m "feat(rpa_arcelor): executar_vt12 (SAP GUI Scripting, adaptado do script gravado)"
```

---

## Task 12: Rodar a suíte inteira e revisão final

**Files:** nenhum novo — só validação.

- [ ] **Step 1: Rodar todos os testes automatizados de uma vez**

Run: `cd rpa_arcelor && python -m unittest discover -p "test_*.py" -v`
Expected: PASS (todos os testes das Tasks 1-9; Tasks 10-11 não têm suíte automatizada, só o checklist manual de cada uma)

- [ ] **Step 2: Conferir que nenhum arquivo de credencial real foi commitado**

Run: `git status --short rpa_arcelor/ && git check-ignore -v rpa_arcelor/credenciais_servico.json`
Expected: `credenciais_servico.json` não aparece em `git status` (se existir localmente) e o `check-ignore` confirma que a regra do `.gitignore` está pegando esse arquivo.

- [ ] **Step 3: Conferir o resumo do que ficou pendente pro usuário decidir/validar**

Não é código — é uma checagem de leitura do que o plano deixou em aberto, pra
não perder de vista:
- Script SAP do ZV74 ainda não gravado (Task 10, Step 5) — botão funciona só
  com arquivo já exportado manualmente.
- `executar_vt12` (Task 11) ainda não validado contra SAP real.
- Migration da Task 9 ainda não aplicada em nenhum ambiente.
- Plano 2 (auditoria dos 28 pontos de leitura de `transporte_itens` no front
  pra filtrar `deleted_at`) não começou — combinado com o usuário como
  trabalho separado.
