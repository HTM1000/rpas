# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Module Overview

**RPA Full Cross (janelas: "RPA Full Cross")** — clone of `rpa_clr`, pointed at the **WMS Jundiaí** Supabase database (same organization, identical table schema). Same SAP GUI Scripting (win32com) architecture as `rpa_clr`. See `../rpa_clr/CLAUDE.md` for the full architecture; only the deltas are documented here.

## Running / Building

```bash
python Genesys_WMS_FULLCROSS.py
pyinstaller Genesys_WMS_FULLCROSS.spec   # single-file EXE → dist/Genesys_WMS_FULLCROSS.exe
```

## Differences vs. rpa_clr

1. **Database** — `SUPABASE_URL` / `SUPABASE_KEY` point at the **WMS Jundiaí** project (service_role key). Tables are identical to `rpa_clr`'s database.

2. **ZV52 filter** — the SAP field and value live in the `ZV52_CAMPO` / `ZV52_VALOR`
   constants (same pattern as `rpa_c3log`), read by `extrair_zv52_para_xls`;
   `caretPosition` is derived from `len(ZV52_VALOR)`. Full Cross uses
   `S_WERKS-LOW = "655"` — the **planta** field, same as `rpa_clr` (which uses `654`).
   The former `S_LGORT-LOW = "ven1"` (depósito) was discarded: it returned no rows.

3. **No transport type filter** — `fluxo_normal` processes **all** pending
   `transportes` rows (`status_consulta_sap = false`), including `devolução`.
   Same as `rpa_clr` and `rpa_c3log`.

4. **Naming** — window titles say "RPA Full Cross"; EXE/script are `Genesys_WMS_FULLCROSS`. A pasta ainda se chama `rpa_venkom` (nome legado, referenciado por `rpa_c3log/CLAUDE.md`).

## Inherited from rpa_clr, extended here

- **Date filter** — the "Data (dd/mm/aaaa)" field filters `transportes` by the day of
  `created_at` (Brasília tz, -03:00). Pre-filled with today's date; clearing it processes
  all pending transports with no date filter. An invalid format warns and aborts the run.
- **Login** — usuário/senha screen: looks the login up in `usuarios` (`is_active = true`),
  then `supabase.auth.sign_in_with_password` with the row's e-mail.
- **Cancel button** — `_cancelar_evento` (a `threading.Event`) is checked per transport
  inside the `fluxo_normal` loop.
- **Paginated ZV52 parse fix** — the SAP export repeats its header block on every page
  break; the parser keeps only the header plus data lines with a matching column count,
  avoiding `ParserError: Expected N fields, saw M`.

## Notes

- The legacy `CredenciaisCLR.json` (Google OAuth) is **not used** by the code and is not bundled by the spec — ignore it.
- `token.json` is unused (no Google Sheets integration; everything is Supabase).
