# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Module Overview

**RPA CLR (Genesys One WMS)** — SAP WMS integration tool for logistics at Tecumseh do Brasil. It bridges SAP WMS and Google Sheets to automate transport/shipping workflows. Unlike other RPA modules in this repo, this one uses SAP GUI Scripting (win32com) instead of PyAutoGUI.

## Running

```bash
python Genesys_WMS_CLR.py
```

`Serial.py` is a standalone predecessor script (serial number upload only); it is superseded by the Serial upload feature built into `Genesys_WMS_CLR.py`.

## Building the Executable

```bash
pyinstaller Genesys_WMS_CLR.spec
```

The spec produces a **single-file EXE** (no separate `_internal/` folder — unlike other modules in this repo). Assets bundled in: `CredenciaisCLR.json`, `image.ico`, `imagelogo.png`. The `token.json` is **not** bundled — it is created externally next to the EXE on first OAuth run.

## Architecture

### Single-file design
All logic lives in `Genesys_WMS_CLR.py`. There are no sub-modules.

### Three Operations (GUI buttons)

1. **Integrar Informações Genesys** (`fluxo_normal`)  
   Reads pending transports (col K ≠ "OK") from `Registro Transportes`, exports `/NZWM3` from SAP for each, parses the XLS export, writes to `INPUT ZWM3` and `Informações Transportes`, then marks col K = "OK".

2. **Validação de Faturamento** (`atualizar_um_transporte_faturado`)  
   For a user-supplied transport number: exports `/NZWM3`, writes to `FATURADO` sheet, updates col T of `Informações Transportes`, then compares against `Expedição Conferencia` (Spreadsheet C1) — printing per-SKU/Remessa match/divergence.

3. **Upload Nº Série** (inline in `acao_serial`)  
   Reads from C1 (`Expedição Conferencia`, filtered to Status="Embarcado"), generates a fixed-format `.txt` file in `C:\RPA\`, uploads via SAP transaction `/NZPCS`, then marks `Upload SAP = OK` in C1.

### SAP Interaction
Uses `win32com.client.GetObject("SAPGUI")` to attach to an already-running SAP GUI session — SAP must be open before running. COM is initialized per-thread via `pythoncom.CoInitialize()` / `CoUninitialize()`.

SAP transactions used:
- `/NZWM3` — Export transport details to XLS
- `/NZPCS` — Upload serial number TXT file

### Google Sheets IDs
| Variable | Spreadsheet |
|---|---|
| `SPREADSHEET_ID` | Main WMS sheet (`15d9oZBw...`) — Registro Transportes, INPUT ZWM3, FATURADO, Informações Transportes |
| `SPREADSHEET_ID_C1` | Expedition/serial sheet (`1Bg243...`) — Expedição Conferencia |

Credentials file: `CredenciaisCLR.json`. OAuth token cached to `token.json` (next to script or EXE).

### XLS Parsing (`parse_zwm3`)
The SAP export is UTF-16 (fallback: Latin-1). Parser extracts remessa numbers (≥6-digit sequences) and SKU/quantity pairs. Quantities are taken as the **last** number on each data line (the "Diferença" column).

### Append with Inherited Formatting (`append_rows`)
Uses `insertDimension` batchUpdate before writing values — this preserves row formatting/conditional formatting from the row above, unlike a plain `values().append()`.

### Thread Safety
All button callbacks run in daemon threads via `@_run_in_thread`. Buttons are disabled for the duration of each operation to prevent concurrent runs. stdout/stderr are redirected to the `ScrolledText` log widget.

## Export Path

Temporary SAP export: `C:\RPA\ZWM3.xls`. The file is deleted after parsing in a `finally` block. Serial number TXTs are also written to `C:\RPA\<transport_padded_10>.txt` and are **not** auto-deleted (SAP transaction opens the file on success via `os.startfile`).

## Transport Number Validation

Transport numbers must be exactly **9 digits** (validated by `validar_transporte` before any SAP or Sheets call).
