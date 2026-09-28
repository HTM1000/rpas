# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Module Overview

**RPA C3Log (Genesys One WMS — C3Log)** — clone of `rpa_venkom`, pointed at the **C3Log** Supabase database (same organization, identical table schema). Same SAP GUI Scripting (win32com) architecture. See `../rpa_clr/CLAUDE.md` for the full architecture; only the deltas are documented here.

## Running / Building

```bash
python Genesys_WMS_C3LOG.py
pyinstaller Genesys_WMS_C3LOG.spec   # single-file EXE → dist/Genesys_WMS_C3LOG.exe
```

## Pending configuration (TODO)

The module is **not runnable yet** — two placeholders must be filled in first:

1. `SUPABASE_URL` / `SUPABASE_KEY` (top of `Genesys_WMS_C3LOG.py`) — currently
   `"PREENCHER_URL_SUPABASE_C3LOG"` / `"PREENCHER_SERVICE_ROLE_KEY_C3LOG"`.
2. `ZV52_VALOR` — currently `"PREENCHER_C3LOG"`. Also confirm `ZV52_CAMPO`
   (`S_LGORT-LOW` for a depósito, `S_WERKS-LOW` for a planta).

## Differences vs. rpa_venkom

1. **Database** — points at the C3Log Supabase project (service_role key).

2. **ZV52 filter** — the SAP field and value are extracted into the `ZV52_CAMPO` /
   `ZV52_VALOR` constants instead of being hardcoded inside `extrair_zv52_para_xls`.
   `caretPosition` is derived from `len(ZV52_VALOR)`.

3. **No transport type filter** — `fluxo_normal` processes **all** pending
   `transportes` rows (`status_consulta_sap = false`), including `devolução`.
   Same as `rpa_clr` and `rpa_venkom`.

4. **Naming** — window titles say "C3Log"; EXE/script are `Genesys_WMS_C3LOG`.

## Inherited from rpa_venkom (not present in rpa_clr)

- **Date filter** — the "Data (dd/mm/aaaa)" field filters `transportes` by the day of
  `created_at` (Brasília tz, -03:00). The field is **pre-filled with today's date**;
  clearing it processes all pending transports with no date filter. An invalid format
  shows a warning and aborts the run.
- **Cancel button** — `_cancelar_evento` (a `threading.Event`) is checked per transport
  inside the `fluxo_normal` loop.
- **Paginated ZV52 parse fix** — the SAP export repeats its header block on every page
  break; the parser keeps only the header plus data lines with a matching column count,
  avoiding `ParserError: Expected N fields, saw M`.

## Notes

- No Google Sheets integration — everything is Supabase. No `CredenciaisCLR.json`,
  no `token.json`.
- Bundled assets (per the spec): `image.ico`, `imagelogo.png`.
