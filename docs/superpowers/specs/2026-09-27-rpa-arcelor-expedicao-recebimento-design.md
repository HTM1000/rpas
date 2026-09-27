# RPA Arcelor — Expedição (ZSD106/VT12/ZV74) e Recebimento (ZSD16)

Data: 2026-09-27
Módulos afetados: `rpa_arcelor/` (neste repo) e `D:\www\react\wmsarcelormital` (repo separado)

## Contexto

O `rpa_arcelor` hoje pede login (e-mail/senha via Supabase Auth) e roda só o ZSD106,
gravando num `MAPEAMENTO` de tabelas ainda vazio (`MODO_GRAVACAO = "simulacao"`). O
usuário colou uma lista de transportes numa caixa de texto única.

O `wmsarcelormital` já tem, em produção, um fluxo MANUAL equivalente:
`ImportarTransportesButton.tsx` — o operador cola a mesma planilha do cliente e o
componente faz parsing + reconciliação + grava no Supabase. Essa lógica já resolve,
hoje, os mesmos três arquivos que o robô vai passar a ler sozinho:

| Transação SAP | O que já existe no front (manual) | Tabela(s) que grava |
|---|---|---|
| ZSD106 | `agendaExpedicaoParser.ts` | `transportes`, `transporte_itens`, `arc_item_ordem_venda` |
| VT12 (sequência de carregamento) | `sequenciaCarregamentoParser.ts` | `arc_transporte_fornecimento` |
| ZV74 (observação de embarque + cond. pagamento) | `observacoesEmbarqueParser.ts` | `arc_observacao_embarque`, `arc_condicao_pagamento_ordem` |
| ZSD16 (recebimento) | não existe ainda em nenhum lado | — |

O Supabase é o MESMO banco de produção usado pelos operadores no navegador (confirmado:
mesmo `ref` do projeto no `supabase/config.toml` do wmsarcelormital e no
`SUPABASE_URL` hardcoded do `Arcelor_WMS.py`). Não é um banco à parte.

## Objetivo

1. Tirar a tela de login do robô; ele autentica sozinho, sem o operador digitar nada.
2. GUI com duas seções — Expedição (botões ZSD106, VT12, ZV74) e Recebimento (botão
   ZSD16, desabilitado/"em breve") — no lugar da caixa de colar única atual.
3. ZSD106, VT12 e ZV74 gravam nas MESMAS tabelas e com as MESMAS regras que o
   `ImportarTransportesButton.tsx` já usa, removendo zero à esquerda dos campos que
   viram chave de junção entre os três arquivos.
4. Regra de peso/unidade do ZSD106: só grava `unidades_pedido` quando
   `Quantidade ≠ Qtde`; quando são iguais, só o peso.
5. Item que some do arquivo do ZSD106 para um transporte: soft-delete via
   `transporte_itens.deleted_at` (coluna nova), espelhando a regra que já existe no
   front (delete real quando nada foi separado ainda → agora vira `deleted_at`;
   zera a quantidade sem apagar quando já tem pré-picking, sem `deleted_at`, igual
   hoje).

## Não-objetivos / fora do escopo agora

- ZSD16 / recebimento automatizado: não temos o script SAP. O botão nasce
  desabilitado; a automação em si é um projeto futuro.
- Rescrever o `ImportarTransportesButton.tsx` para usar `deleted_at` também no
  caminho manual — ele continua com o comportamento atual (delete real ou zera).
  O soft-delete é um mecanismo introduzido especificamente para o caminho do robô.
- Corrigir a inconsistência preexistente do front (item "Achados" abaixo) fora do
  que o robô precisa para si mesmo.
- Build/EXE novo — só o código; o build já é processo conhecido (`BUILD` não existe
  ainda pra esse módulo, só o `.spec`; roda-se `pyinstaller Arcelor_WMS.spec` quando
  for a hora).

## Decisões de design e porquês

**Autenticação de serviço silenciosa, não RLS aberto para `anon`.** As tabelas
`transportes`/`transporte_itens` têm RLS por CARGO (`admin` ou `conferente` para
INSERT/UPDATE) — são tabelas de produção que os operadores usam ao vivo. Abrir para
`anon` tiraria o controle por cargo e o rastreio de autoria dessas duas tabelas
específicas. Em vez disso: uma conta de serviço fixa (ex. `robo.zsd106@...`) com role
`conferente` já atribuída faz login sozinha, uma vez, no início do programa — sem
tela, sem o operador digitar nada. Credenciais ficam num arquivo de config local, fora
do código-fonte e fora do git, mesmo padrão de cuidado que os outros módulos já usam
para `CredenciaisOracle.json`.

**Reuso das tabelas e regras do `ImportarTransportesButton.tsx`, não uma lógica
paralela.** As colunas, chaves de conflito de upsert e a regra peso-vs-unidade
(`porUnidade = unidades !== peso`) já existem e já são usadas em produção pelo
caminho manual. Reimplementar do zero seria duplicar regra de negócio em dois
lugares que podem divergir. O robô grava como se fosse "mais um operador colando a
planilha" — do ponto de vista do WMS, é indistinguível.

**Zero à esquerda: normalizar em TODOS os campos que são chave de junção, inclusive
onde o front hoje ainda não normaliza.** VT12 (`arc_transporte_fornecimento`) e ZV74
(`arc_observacao_embarque`, `arc_condicao_pagamento_ordem`) já gravam
`fornecimento`/`ordem_venda` SEM zero à esquerda. O parser atual do ZSD106
(`agendaExpedicaoParser.ts`) grava esses mesmos campos em `arc_item_ordem_venda` COM
zero à esquerda — uma inconsistência preexistente no front, não introduzida por este
projeto. O robô vai remover zero à esquerda também nesses campos do ZSD106, pra casar
com o que VT12/ZV74 já gravam (é assim que os três arquivos se cruzam pelo mesmo
fornecimento/ordem de venda). Campos normalizados: `numero_transporte`, `Material`
(SKU), `Fornecimento`, `Doc. Modelo` (= ordem de venda).

**`deleted_at` só para o que o robô apaga, espelhando a regra de pré-picking que já
existe.** Pedido explícito do usuário, confirmado após consultar o comportamento
atual: se nada daquele item ainda foi separado no depósito, marca `deleted_at`
(equivale ao delete de hoje); se já tem material em pré-picking, mantém visível e
zera a quantidade, sem `deleted_at` — não esconde um problema de estoque já separado.

## Arquitetura / componentes

```
rpa_arcelor/Arcelor_WMS.py
├── autenticação de serviço (substitui criar_tela_login)
├── GUI: 2 seções (Expedição / Recebimento), 4 botões (3 ativos + ZSD16 desabilitado)
├── executar_zsd106()        [existe, mantém]
├── executar_vt12()          [novo — mesmo padrão de SAP GUI Scripting]
├── executar_zv74()          [novo — script SAP ainda por gravar/validar]
├── ler_planilha()           [existe, reaproveitado pelos 3]
└── gravar_no_banco_*()      [substitui o MAPEAMENTO genérico por 3 funções
                               específicas, uma por transação, cada uma
                               espelhando seu parser TS equivalente]

wmsarcelormital/
├── supabase/migrations/..._transporte_itens_deleted_at.sql   [novo]
└── pontos de leitura de transporte_itens                     [precisam filtrar
                                                                 deleted_at is null
                                                                 — levantamento
                                                                 completo no plano]
```

## Fluxo de dados por transação

### ZSD106 (expedição) — `transportes` + `transporte_itens` + `arc_item_ordem_venda`

Planilha: `N° Transporte | Doc. Modelo | Fornecimento | Material | Descr Material |
ID MA Transporte | Lote | Quantidade | Qtde | Nota Fiscal | Nome`.

Por transporte (`N° Transporte`, sem zero à esquerda):
- `transportes`: upsert por `numero_transporte` — `tipo='expedicao'`,
  `status='agendado'`, `hora_agenda=null`. NÃO sobrescrever campos que o operador
  edita (`placa_confirmada`, campos de encerramento, etc.) — só os campos que o ZSD106
  realmente informa.
- Por item (`Material` = sku, sem zero à esquerda):
  - `peso = Quantidade`, `unidade = Qtde`.
  - Se `peso == unidade`: `transporte_itens.quantidade_pedido = peso`,
    `unidades_pedido = null`, `separa_por_unidade = false`.
  - Se `peso != unidade`: `quantidade_pedido = peso`, `unidades_pedido = unidade`,
    `separa_por_unidade = true`.
  - Reconciliação contra o que já está gravado para esse transporte:
    - igual → não mexe.
    - diferente (pra mais ou pra menos) → `update`.
    - não existe ainda → `insert`.
    - existia e sumiu do arquivo → ver regra de `deleted_at` acima.
  - `arc_item_ordem_venda`: uma linha por quebra de `Fornecimento`/`Doc. Modelo`
    (= ordem de venda), ambos sem zero à esquerda, `quantidade_kg`, `unidades`,
    `ordem` = posição de aparição na planilha.

### VT12 (expedição, sequência de carregamento) — `arc_transporte_fornecimento`

Arquivo: texto tab-separated (`vt12.txt`), cabeçalho "Transportes e fornecimento".
Estrutura hierárquica: linha de transporte (nº transporte, rota, peso total,
transportadora) seguida de N linhas de fornecimento (nº fornecimento COM zero à
esquerda no arquivo real, status, cliente/destinatário, endereço, UF, incoterm, peso,
datas).

Grava, por transporte (delete-then-insert, igual ao `sequenciaCarregamentoParser.ts`):
`transporte_id` (resolvido pelo `numero_transporte` sem zero), `fornecimento` (sem
zero à esquerda), `ordem_carregamento` (posição no arquivo), `cliente`, `destino`,
`uf`, `peso_kg`.

Script SAP: mesma transação e navegação do `Script1 - VT12.vbs` já gravado (vt12 →
seleção múltipla de transporte por `K_TKNUM` → tela de planejamento → imprime/salva
como arquivo local). Precisa ser adaptado pro padrão Python/`win32com` que
`executar_zsd106` já usa (tratamento de diálogos por reconhecimento de controle, não
"aperta OK 3x às cegas").

### ZV74 (expedição, observação de embarque + condição de pagamento)

Arquivo: `.xlsx` de verdade, colunas `Desc Cond Pagto | Ordem Vendas | Número do
fornecimento | Texto Embarque | Texto Embarque.1`.

Grava (mesma lógica do `observacoesEmbarqueParser.ts`):
- `arc_observacao_embarque`: upsert por `fornecimento` (sem zero à esquerda) —
  `texto`, `atualizado_em`, `atualizado_por` (usuário de serviço).
- `arc_condicao_pagamento_ordem`: upsert por `ordem_venda` (= "Ordem Vendas", sem
  zero à esquerda) — `descricao`, `atualizado_em`, `atualizado_por`.

**Pendência conhecida:** não existe ainda um `Script-ZV74.vbs` gravado — vai precisar
gravar e validar em SAP real (mesma cautela que o `CLAUDE.md` já pede pro export do
ZSD106: gravar só essa parte, uma vez, limpa, e validar o formato do arquivo antes de
confiar no parsing).

### ZSD16 (recebimento)

Fora de escopo. Botão existe na tela, desabilitado, texto "em breve".

## GUI (`Arcelor_WMS.py`)

- Remove `criar_tela_login()` e a checagem `if usuario:` do `__main__`. No lugar,
  autentica com a conta de serviço logo no início (mesma função
  `autenticar_usuario`, chamada com credenciais fixas lidas de um arquivo de config
  local em vez de campos digitados). Se a autenticação de serviço falhar, mostra erro
  claro e não abre a GUI principal (falha configuração ≠ falha de operador).
- A caixa única de "Cole aqui os transportes" vira duas seções empilhadas (Expedição
  em cima, Recebimento embaixo, mesma janela): **Expedição** (caixa de colar +
  botões "Rodar ZSD106" / "Rodar VT12" / "Rodar ZV74", cada um dispara seu próprio
  fluxo, independente dos outros) e **Recebimento** (caixa de colar + botão "Rodar
  ZSD16" desabilitado).
- Os três botões de expedição continuam usando o mesmo parser de transportes
  (`parse_transportes`) e o mesmo padrão de log/threading que já existe.

## Migração de banco e frontend

- Migration nova em `wmsarcelormital/supabase/migrations/`:
  `ALTER TABLE public.transporte_itens ADD COLUMN deleted_at timestamptz;`
- Todo ponto do front que lê `transporte_itens` (via `arc('transporte_itens')` ou
  `.from('transporte_itens')`) precisa do filtro `.is('deleted_at', null)`. O
  levantamento completo desses pontos fica para o plano de implementação (não foi
  enumerado agora) — é um passo obrigatório antes de ativar a gravação real, senão
  itens "excluídos" pelo robô continuam aparecendo pro operador.
- RLS de UPDATE em `transporte_itens` já cobre a role `conferente` — a conta de
  serviço do robô não precisa de policy nova, só precisa ter essa role atribuída em
  `user_roles`.

## Erros e modo de teste

- Mantém o padrão `MODO_GRAVACAO = "simulacao"` (lê e mostra o que faria, não grava)
  até validar contra planilhas reais do SAP — mas agora por transação
  (`MODO_GRAVACAO_ZSD106`, `_VT12`, `_ZV74`, já que cada uma valida em momento
  diferente conforme os scripts forem gravados/validados no SAP real).
- Falha de export (arquivo não gerado, diálogo que não fecha) já tem tratamento no
  ZSD106 (`_exportar_grid`) — VT12/ZV74 devem seguir o mesmo padrão de detectar e
  reportar, não travar a GUI.
- `_sap_fechar_popups` já limpa popups de execução anterior — reaproveitar antes de
  cada uma das 3 transações, não só do ZSD106.

## Riscos / pendências que já existiam e continuam valendo

- Export do ZSD106 nunca rodou contra SAP real (`FORMATO_LISTBOX = "33"` vem de
  gravação, precisa validar).
- `ZSD106 TESTE 21.09.2026.XLSX` (arquivo de amostra) veio sem zero à esquerda porque
  o Excel converteu os códigos em número — não é garantia de como o export real do
  SAP vai vir (tende a ser texto tab-separated, igual ao VT12). A remoção de zero à
  esquerda tem que funcionar tanto pra texto quanto pra número já convertido.
- Script ZV74 não existe — precisa ser gravado em SAP real antes de qualquer teste
  ponta a ponta dessa transação.

## Teste

- `MODO_TESTE` (já existe no padrão dos outros RPAs, ainda não neste arquivo) deve
  cobrir os 3 fluxos sem PyAutoGUI/SAP real, usando os arquivos de amostra já
  fornecidos (`vt12.txt`, `zv74.XLSX`, `ZSD106 TESTE 21.09.2026.XLSX`) para validar
  parsing + regra peso/unidade + reconciliação (incluindo `deleted_at`) contra um
  Supabase de teste antes de apontar pro banco de produção.
- Autenticação de serviço: testar falha (credencial errada/rede fora) não deixa a
  GUI abrir num estado que pareça funcional.
