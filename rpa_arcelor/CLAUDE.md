# CLAUDE.md

Módulo **RPA Arcelor Mittal (Hawk Tech WMS)** — copia o padrão do `rpa_clr` (SAP GUI Scripting via win32com + Supabase + Tkinter), automatizando ZSD106/VT12/ZV74 (expedição). ZSD16 (recebimento) ainda não existe.

## Fluxo

1. Autenticação de serviço silenciosa no início do programa (sem tela de login pro operador) — `autenticar_usuario` chamado com credenciais fixas lidas de `credenciais_servico.json` (ver `auth_servico.carregar_credenciais_servico`). Se falhar, mostra erro e a GUI principal não abre.
2. GUI com 2 seções: **Expedição** (caixa de colar + botões "Rodar ZSD106" / "Rodar VT12" / "Rodar ZV74", cada um independente) e **Recebimento** (caixa de colar + botão "Rodar ZSD16 (em breve)", desabilitado).
3. `executar_zsd106`: abre `/nzsd106`, preenche os filtros, **cola os transportes pela área de transferência** (`btn[24]` do popup de seleção múltipla `S_TKNUM`), F8, exporta o ALV (`&MB_EXPORT` > `&XXL`) para `C:\RPA\zsd106.xlsx`. `executar_vt12` faz o equivalente pro VT12 (sequência de carregamento). ZV74 não tem automação SAP ainda — lê um `.xlsx` exportado manualmente.
4. `ler_planilha`/`ler_linhas_vt12` leem o arquivo (decidem o formato pelo conteúdo, não pela extensão); `zsd106_parser`/`vt12_parser`/`zv74_parser` fazem o parsing puro; `zsd106_writer.gravar_zsd106`/`vt12_writer.gravar_vt12`/`zv74_writer.gravar_zv74` gravam DIRETO no Supabase de produção (upsert/reconciliação), sem gate nenhum.

## Estado atual (LER ANTES DE MEXER)

- **Sem modo simulação — o robô grava de verdade em produção a cada execução.** Decisão explícita do usuário (27/09/2026): a v1 vai direto pra gravação real; não existe `MODO_GRAVACAO`/`MAPEAMENTO` nem qualquer flag por transação que bloqueie o write antes de rodar. Os 3 botões de expedição chamam `gravar_zsd106`/`gravar_vt12`/`gravar_zv74` diretamente. Isso é intencional, não uma pendência — mas significa que qualquer teste manual clicando nos botões da GUI real grava em produção; use `unittest`/`supabase_fake.py` pra testar sem tocar no banco de verdade.
  - **Consequência conhecida e aceita:** como não há simulação e o front-end (wmsarcelormital) ainda não filtra `deleted_at` (isso é o "Plano 2", trabalho futuro separado), um item que o robô soft-deleta (`transporte_itens.deleted_at` marcado) continua aparecendo com a quantidade cheia no app ao vivo (Agenda, Conferência, Separação etc.) até o Plano 2 subir. Não é bug — é consequência direta de ir pra produção sem modo simulação (decisão do usuário, 27/09/2026) — só deixando registrado pra ninguém ser pego de surpresa.
- **Export do ZSD106 nunca foi rodado num SAP real.** O script gravado (`Script-ZSD106.vbs`) tinha 4 tentativas de export e caminhos de teste; `_exportar_grid` trata os diálogos por reconhecimento do controle, e `FORMATO_LISTBOX = "33"` vem da gravação e precisa ser validado. Se o export falhar, regravar SÓ a parte do export, uma vez, limpa. Consequência direta: `parse_numero_zsd106` (`normalizacao.py`) ainda não sabe distinguir, para um valor sem vírgula tipo "1.496", se é milhar (1496) ou decimal (1,496kg) — o formato real do export do ZSD106 continua sem validar contra um SAP de verdade. Uma tentativa anterior de rejeitar esse caso como "ambíguo" foi revertida (commit seguinte ao 518ef31): o regex de ambiguidade batia com TODO peso normal abaixo de 1000kg com 3 casas decimais (o caso comum, não o raro), rejeitando a maioria dos pesos válidos. Por ora trata como decimal (mesma regra de sempre, sem adivinhação nem rejeição) — **risco conhecido e aceito** até essa validação acontecer contra SAP real.
- **VT12** (`Script1 - VT12.vbs` / `executar_vt12`) também ainda não foi validado contra SAP real.
- **ZV74**: não existe `Script-ZV74.vbs` gravado ainda — precisa gravar e validar em SAP real antes de qualquer automação ponta a ponta dessa transação; por ora só lê um `.xlsx` exportado manualmente para `C:\RPA\zv74.xlsx`.
- **Pré-voo de RLS/permissões pendente antes da primeira rodada real em produção:** confirmar que a role da conta de serviço tem SELECT em `movimentacao_armazenagem` e INSERT/UPDATE nas tabelas `arc_*`/`transportes`/`transporte_itens` em staging. Sem isso, uma negação silenciosa de SELECT em `movimentacao_armazenagem` faria `_buscar_pre_picking` (`zsd106_writer.py`) devolver vazio pra tudo e todo item que sumiu do arquivo seria apagado em vez de zerado — ver o comentário na função.

## Banco (Supabase, projeto da Arcelor, separado do CLR)

- O projeto NÃO é vazio: é o banco do WMS da Arcelor em uso. Tabelas gravadas pelo robô: `transportes`, `transporte_itens`, `arc_item_ordem_venda` (ZSD106), `arc_transporte_fornecimento` (VT12), `arc_observacao_embarque`/`arc_condicao_pagamento_ordem` (ZV74). `arc_transporte` é órfã — nunca usar. Upsert/reconciliação (não apagar e reinserir a esmo) e **nunca sobrescrever campos que o operador edita no sistema** (placa confirmada, status etc.).
- **Só a chave `anon` vai no EXE.** Ela não lê/grava nada sozinha; depois do login de serviço o RPA usa o JWT da conta de serviço e o RLS decide (role `conferente`). Nunca embutir a `service_role` (ela ignora o RLS e é extraível do EXE).
- Manter **um único** cliente Supabase autenticado (`_supabase`). Criar um cliente novo perde o login.
- `deleted_at` em `transporte_itens`: quando um item some do arquivo do ZSD106 e não tem pré-picking, o robô marca `deleted_at` (soft-delete) em vez de apagar; se já tem pré-picking, zera a quantidade sem `deleted_at`. Um transporte cuja leitura teve linha inválida não tem itens sumidos apagados/zerados nessa rodada (proteção contra falso positivo de "sumiu" por erro de parsing).

## Detalhes que já deram problema

- **Clipboard:** `_copiar_para_clipboard` usa ctypes. O `SetClipboardData` do pywin32 falhava (erro 998/6) com texto de uma linha só, ou seja, colar um único transporte quebraria.
- **`/n` no okcd:** sem `/nzsd106` o SAP só troca de transação se estiver na tela inicial.
- **Planilha do SAP** costuma ser texto separado por tab com extensão `.xlsx`; `pd.read_csv` quebra com `Expected N fields`. A leitura é manual.
- Datas do ZSD106: o script gravado usava só o ano corrente; aqui vai de 01.01 do ano passado a 31.12 do atual, para não perder transportes de dezembro.

## Rodar / Build

```bash
python Arcelor_WMS.py
pyinstaller Arcelor_WMS.spec        # onefile -> dist\HawkTech_WMS_ARCELOR.exe
```

O onefile extrai no `%TEMP%` a cada abertura (abre devagar) e foi o formato que o CrowdStrike do cliente bloqueou no CLR; se acontecer aqui, usar onedir (ver `rpa_clr/Genesys_WMS_CLR.spec`).
