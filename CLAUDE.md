# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains **RPA (Robotic Process Automation) systems** for Tecumseh do Brasil that automate Oracle ERP operations. The main systems are:

1. **RPA Ciclo (Genesys)** - Orchestrates complete automation cycles combining Oracle data entry with material workbench processing
2. **RPA Oracle** - Automates data entry into Oracle ERP from Google Sheets
3. **RPA Bancada** - Extracts and processes material workbench data from Oracle
4. **RPA NFRi** - Extracts NFRi (fiscal invoice) data from web system to Google Sheets

## Architecture

### Multi-Module Design
The system uses a **modular architecture** where each RPA is independent but can be orchestrated:

- **rpa_ciclo/** - Main orchestration module (calls rpa_oracle and rpa_bancada)
- **rpa_oracle/** - Standalone Oracle data entry automation
- **rpa_bancada/** - Standalone Oracle data extraction automation
- **rpa_nfri/** - Standalone web data extraction automation

### Key Components

#### 1. GUI Layer (Tkinter)
- `RPA_Ciclo_GUI_v2.py` - Main cycle GUI with file history
- `RPA_Oracle.py` - Oracle RPA GUI
- `RPA_Bancada_GUI.py` - Material workbench GUI
- All GUIs use threading to avoid blocking the UI during automation

#### 2. Automation Logic
- `main_ciclo.py` - Complete cycle orchestration (6-step process)
- Uses PyAutoGUI for screen automation (mouse clicks, keyboard input)
- Implements OCR validation using Tesseract to verify data entry accuracy
- Image-based error detection (qtd_negativa.png, ErroProduto.png)

#### 3. Google Sheets Integration
- **Two separate Google Sheets modules:**
  - `google_sheets_ciclo.py` - For cycle execution logs (SPREADSHEET_ID: 14yUMc12iCQxqVzGTBvY6g9bIFfMhaQZ26ydJk_4ZeDk)
  - `google_sheets_manager.py` - For material workbench data (SPREADSHEET_ID: 1UgJWxmnYzv-FVTT4rrrVEx3J_MNXZsctwrPSTyyylPQ)
- OAuth2 authentication with cached tokens (token.json)
- Credentials stored in CredenciaisOracle.json (embedded in executable)

#### 4. Configuration System
- `config.json` - Screen coordinates and timing configurations
- All pixel coordinates are resolution-dependent (configured for 1440x900)
- Timing configurations in seconds for delays between operations

#### 5. Cache & State Management
- `processados.json` - Persistent cache to prevent duplicate Oracle entries
- Session-based tracking for export files
- Thread-safe operations using locks

## Build System

### Creating Executables

**Primary build script:** `BUILD_GENESYS.bat` (for RPA Ciclo)

```bash
cd rpa_ciclo
BUILD_GENESYS.bat
```

This script:
1. Verifies Python and PyInstaller installation
2. Validates required images exist (qtd_negativa.png, ErroProduto.png)
3. Cleans previous builds
4. Runs PyInstaller with Genesys.spec
5. Validates the build
6. Optionally copies to Desktop

**Important:** Always distribute the **entire folder** (dist/Genesys/), not just the .exe. The executable depends on:
- `_internal/informacoes/` - Error detection images
- `_internal/tesseract/` - OCR engine
- `config.json` - Coordinates and settings
- `CredenciaisOracle.json` - Google API credentials

### PyInstaller Specs
Each RPA module has its own .spec file:
- `rpa_ciclo/Genesys.spec` - Main cycle executable
- Other modules use similar patterns

## Critical Implementation Details

### RPA Ciclo 6-Step Process (main_ciclo.py)

1. **Transfer Subinventory** - Navigate to transfer screen
2. **Fill Type (SUB)** - Enter transaction type
3. **Select Employee (Wallatas)** - Choose responsible person
4. **RPA Oracle Execution** - Process Google Sheets data into Oracle
   - Read pending items from Google Sheets
   - For each item: fill fields, validate with OCR, save (Ctrl+S)
   - Handle errors: qtd_negativa.png (continue), ErroProduto.png (STOP)
   - Update Google Sheets with status
5. **Navigation to Workbench** - Close modals, navigate menus
   - Critical step: Must click "Janela" (Window) to give focus
   - Coordinates: Janela (340,40), Menu (376,127), Bancada (598,284)
6. **RPA Bancada Execution** - Extract and process workbench data
   - Click Detalhado, wait 2 minutes for data load
   - Copy grid data to clipboard
   - Process with pandas and send to Google Sheets

### Error Handling Strategy

**Image-based Error Detection:**
- `qtd_negativa.png` - Negative quantity error → Press Enter + Ctrl+S, continue
- `ErroProduto.png` - Invalid product error → Mark as "PD", STOP application

**OCR Validation Retry:**
- On OCR failure: Mark as "Erro OCR - Tentar novamente"
- Do NOT add to cache (allows reprocessing)
- Next cycle automatically retries

### Security Considerations

**Credentials Management:**
- `CredenciaisOracle.json` - Google API credentials (NEVER commit to git)
- `token.json` - OAuth token generated on first run
- Both are embedded in executables but token.json is also created externally

**FAILSAFE:**
- PyAutoGUI FAILSAFE enabled (move mouse to 0,0 to emergency stop)
- All automation checks `_rpa_running` flag before each operation

## Common Development Tasks

### Running in Development Mode

```bash
# RPA Ciclo
cd rpa_ciclo
python RPA_Ciclo_GUI_v2.py

# RPA Oracle
cd rpa_oracle
python RPA_Oracle.py

# RPA Bancada
cd rpa_bancada
python main.py
```

### Testing Mode

In `main_ciclo.py`, set flags:
```python
MODO_TESTE = True   # Simulates operations without PyAutoGUI
PARAR_QUANDO_VAZIO = True  # Stops when no items to process
```

### Adjusting Screen Coordinates

1. Run `mouse_position_helper.py` to capture coordinates
2. Update `config.json` with new coordinates
3. Test carefully before deploying

### Debugging

Look for debug logs in format:
```
[DEBUG] _rpa_running=True | Tentando clicar em 'Janela'
[PASSO X/6] Description...
🛑 [PASSO X/6] FAILSAFE ACIONADO ao clicar em 'X'!
```

## Dependencies

**Core:**
- pyautogui - Screen automation
- pyperclip - Clipboard operations
- keyboard - Keyboard shortcuts
- pandas - Data processing

**Google Integration:**
- google-auth, google-auth-oauthlib
- google-api-python-client

**OCR:**
- pytesseract - OCR engine wrapper
- Pillow - Image processing
- Tesseract-OCR binary (C:\Program Files\Tesseract-OCR\ or local tesseract/)

**GUI:**
- tkinter (built-in)
- PIL/Pillow - Image display

## Important File Locations

**Development:**
- Source code: `rpa_*/` folders
- Configuration: `rpa_ciclo/config.json`
- Credentials: `rpa_*/CredenciaisOracle.json` (gitignored)

**Runtime (Executables):**
- Build output: `rpa_ciclo/dist/Genesys/`
- Persistent cache: `processados.json` (next to .exe)
- OAuth token: `token.json` (next to .exe)

## Git Status Notes

The repository shows many deleted files in rpa_ciclo/ (test files, old docs, etc). This is expected cleanup. Key files remaining:
- `main_ciclo.py` - Core logic
- `RPA_Ciclo_GUI_v2.py` - GUI
- `google_sheets_ciclo.py`, `google_sheets_manager.py` - Integrations
- `BUILD_GENESYS.bat` - Build script
- `config.json` - Configuration
- `README_PRINCIPAL.md` - Main documentation

## Coordinates Reference (config.json)

All coordinates are for **specific screen resolution** (likely 1440x900 @ 100% scale). When coordinates don't work:
1. Check screen resolution and scaling
2. Use mouse_position_helper.py to recapture
3. Update config.json
4. Rebuild if using executable

**Critical coordinates for Etapa 6 (Step 6):**
- `navegador_janela`: (340, 40) - "Janela" menu click
- `navegador_menu`: (376, 127) - Navigation menu
- `tela_07_bancada_material`: (598, 284) - "4. Bancada de Material" (double-click)

## Timing Configurations

From `config.json`:
- `entre_cliques`: 3s - Between UI clicks
- `apos_modal`: 5s - After modal closes
- `apos_rpa_oracle`: 4s - After Oracle RPA completes
- `apos_rpa_bancada`: 4s - After Bancada RPA completes
- `ciclo_completo`: 1800s (30 min) - Full cycle duration

## When Editing Code

1. **Coordinate changes** - Always update config.json, avoid hardcoding
2. **Google Sheets IDs** - Different modules use different spreadsheets
3. **OCR paths** - Tesseract can be local (tesseract/) or system-installed
4. **Thread safety** - Use locks when modifying shared state
5. **Error detection images** - Must be in informacoes/ and included in .spec
6. **Encoding** - All files use UTF-8, Windows console needs special handling

## Testing Checklist

Before deploying builds:
1. ✅ Test in MODO_TESTE first
2. ✅ Verify all images exist in informacoes/
3. ✅ Check config.json coordinates match target screen
4. ✅ Test Google Sheets authentication
5. ✅ Verify cache (processados.json) working
6. ✅ Test OCR validation on sample screens
7. ✅ Confirm FAILSAFE works (move mouse to corner)
8. ✅ Build with BUILD_GENESYS.bat
9. ✅ Test executable on target machine
10. ✅ Distribute entire folder, not just .exe
