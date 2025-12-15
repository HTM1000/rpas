# Implementation Plan: Modal Error Detection & Login Validation

**Branch**: `001-modal-error-detection` | **Date**: 2025-12-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-modal-error-detection/spec.md`

## Summary

Enhance RPA Inventário with robust error modal detection and login validation. After filling Item, Endereço, SubInventário, and UDM fields, the system will check for error modals with specific titles and **STOP execution completely** if detected. Additionally, login validation will occur before every save operation to prevent data loss from expired sessions. The system will support environment-specific error images for test and production environments.

**Technical Approach**: Extend existing PyAutoGUI image-based detection with checkpoint-based error modal scanning. Leverage existing localizar_imagem() function with configurable error image sets. Implement detection checkpoints after each critical field entry and before save operations.

---

## ⚠️ CRITICAL BEHAVIOR: RPA STOPS ON ANY ERROR

**IMPORTANTE**: Quando **QUALQUER** erro modal for detectado (Item, Endereço, SubInventário, UDM, ou Login Expirado), o RPA **PARA COMPLETAMENTE**:

✅ **O que acontece quando erro é detectado:**
1. RPA detecta imagem do erro modal
2. Loga erro específico com checkpoint onde ocorreu
3. Marca item na planilha com status do erro (ex: "Erro: Item Inexistente")
4. **Lança Exception para parar execução completamente**
5. RPA **NÃO** continua processando próximo item
6. Usuário deve resolver erro manualmente e executar RPA novamente

❌ **O que NÃO acontece:**
- RPA NÃO pula o item e continua
- RPA NÃO marca como "pulado" e segue
- RPA NÃO tenta resolver erro automaticamente
- RPA NÃO processa outros itens da lista

**Justificativa**: Erros modais indicam problemas de dados que podem causar inconsistências. Parar imediatamente previne erros em cascata e garante integridade dos dados.

---

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: PyAutoGUI 0.9.54, Pillow (image processing), pyperclip, keyboard
**Storage**: Google Sheets (existing google_sheets_inventario.py), config.json for configuration
**Testing**: Manual testing with test environment (elementos/teste/ images)
**Target Platform**: Windows 10/11 desktop automation
**Project Type**: Single desktop automation application
**Performance Goals**: Error detection must add <3 seconds total overhead per item (5 checkpoints × ~0.5-0.6s each)
**Constraints**: Image detection confidence ≥0.8, detection timeout 2-3s per checkpoint to balance speed vs accuracy
**Scale/Scope**: Processes hundreds of inventory items per batch; error detection must not significantly slow throughput

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Selenium-First
**Status**: ⚠️ NOT APPLICABLE - This project uses PyAutoGUI (desktop automation), not Selenium (web automation)
**Justification**: RPA Inventário automates a desktop application (Oracle client), not a web interface. PyAutoGUI is the appropriate technology for screen-based automation. While this violates the Selenium-First principle, the principle does not apply to desktop application automation.
**Note**: If future iterations move to Oracle web interface, migration to Selenium will be required per constitution.

### II. Configuration-Driven
**Status**: ✅ PASS
**Evidence**:
- Error detection timeouts will be configured in config.json
- Error image file names will be configurable (not hardcoded)
- Confidence levels for image detection will be in config.json
- Environment selection (test vs prod) already driven by modo_teste flag

**Implementation**:
```json
"erro_detection": {
  "timeout_por_checkpoint": 2,
  "confianca_padrao": 0.8,
  "checkpoints": {
    "after_item": ["erro_item_inexistente.png"],
    "after_endereco": ["erro_endereco_inexistente.png"],
    "after_subinventario": ["erro_subinventario_inexistente.png"],
    "after_udm": ["erro_udm_inexistente.png"],
    "before_save": ["login_expirado.png"]
  }
}
```

**Nota**: As imagens de erro já existem em `elementos/` e `elementos/teste/`

### III. Standalone Build (NON-NEGOTIABLE)
**Status**: ✅ PASS
**Evidence**:
- Error images will be included in PyInstaller spec via `datas` parameter
- elementos/ and elementos/teste/ directories will be bundled
- No new dependencies required (uses existing PyAutoGUI/Pillow)
- BUILD_INVENTARIO.bat will validate error images exist before build

**Build Changes Required**:
- Update Inventario.spec to include elementos/teste/ directory
- Add validation step in BUILD_INVENTARIO.bat to check error image files exist

### IV. GUI Reliability
**Status**: ✅ PASS
**Evidence**:
- Error detection runs in automation thread (not GUI thread)
- Pause on error uses existing stop_rpa() mechanism
- ESC emergency stop already implemented and will work during error detection
- Real-time logging will report each checkpoint status

**No changes required** - existing threading model supports error detection.

### V. Error Detection & Visibility
**Status**: ✅ PASS (Enhanced by this feature)
**Evidence**:
- Each checkpoint will log: "🔍 Checkpoint: after_item - verificando erros..."
- Modal detection will log specific error: "🚨 ERRO DETECTADO: Item Inexistente (erro_item_inexistente.png)"
- Login validation will log: "✅ Login OK" or "🚨 LOGIN EXPIRADO"
- Pause messages will guide user: "🛑 RPA PAUSADO - Resolva o erro e execute novamente"

**This feature actively improves Error Detection & Visibility principle compliance.**

## Project Structure

### Documentation (this feature)

```text
specs/001-modal-error-detection/
├── plan.md              # This file
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output - modal detection patterns
└── contracts/           # N/A for desktop automation (no API contracts)
```

### Source Code (repository root)

```text
rpa_inventario/
├── main_inventario.py           # MODIFY: Add checkpoint error detection
├── config.json                  # MODIFY: Add erro_detection config section
├── elementos/                   # ALREADY EXISTS with error images
│   ├── erro_item_inexistente.png          # ✅ EXISTS
│   ├── erro_endereco_inexistente.png      # ✅ EXISTS
│   ├── erro_subinventario_inexistente.png # ✅ EXISTS
│   ├── erro_udm_inexistente.png           # ✅ EXISTS
│   ├── login_expirado.png                 # ✅ EXISTS
│   └── (other UI element images...)
├── elementos/teste/             # ALREADY EXISTS with test error images
│   ├── erro_item_inexistente.png          # ✅ EXISTS (test version)
│   ├── erro_endereco_inexistente.png      # ✅ EXISTS (test version)
│   ├── erro_subinventario_inexistente.png # ✅ EXISTS (test version)
│   ├── erro_udm_inexistente.png           # ✅ EXISTS (test version)
│   ├── login_expirado.png                 # ✅ EXISTS (test version)
│   └── (other test images...)
├── Inventario.spec              # MODIFY: Include elementos/teste/ in datas
└── BUILD_INVENTARIO.bat         # MODIFY: Validate error images exist

tests/                           # N/A - manual testing only per constitution
```

**Structure Decision**: Single project structure maintained. All changes are within existing main_inventario.py module. No new files created - follows principle of minimal complexity.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Selenium-First principle (uses PyAutoGUI instead) | Desktop application automation requires screen-based interaction, not web automation | Selenium cannot automate desktop applications. Oracle client is not a web interface in current deployment. |

## Phase 0: Research

**Goal**: Understand optimal patterns for checkpoint-based error detection without degrading performance.

### Research Tasks

1. **Analyze current image detection performance**
   - Measure average localizar_imagem() execution time with varying timeouts
   - Determine optimal timeout for error modals (balance detection vs speed)
   - Document: Current detection takes ~0.3-0.5s with timeout=2s

2. **Identify error modal timing patterns**
   - Research: When do Oracle error modals appear after field entry?
   - Do modals appear immediately or after network round-trip?
   - Document: Recommended wait time before checking for modal (if any)

3. **Error image naming convention**
   - Research: Best practices for naming error detection images
   - Pattern: erro_{field}_{error_type}.png or erro_{error_type}_{field}.png?
   - Document: Chosen convention and rationale

4. **Checkpoint placement strategy**
   - Research: Should checkpoint run immediately after field entry or after TAB?
   - Trade-off: Earlier detection vs allowing field validation to complete
   - Document: Optimal checkpoint timing per field type

**Output**: research.md documenting findings and decisions

## Phase 1: Design & Implementation Details

**Prerequisites**: research.md complete

### Design Decisions

#### 1. Checkpoint Function Design

```python
def verificar_erro_modal(checkpoint_name: str, timeout: int = 2) -> Optional[str]:
    """
    Verifica se um modal de erro apareceu na tela

    Args:
        checkpoint_name: Nome do checkpoint (after_item, after_endereco, etc.)
        timeout: Tempo máximo para procurar modal

    Returns:
        Nome da imagem do erro detectado ou None
    """
    config_erro = CONFIG.get('erro_detection', {})
    imagens_erro = config_erro.get('checkpoints', {}).get(checkpoint_name, [])
    confianca = config_erro.get('confianca_padrao', 0.8)

    log(f"🔍 Checkpoint '{checkpoint_name}': verificando {len(imagens_erro)} erros possíveis...")

    for imagem_erro in imagens_erro:
        posicao = localizar_imagem(imagem_erro, confianca=confianca, timeout=timeout)
        if posicao:
            return imagem_erro

    return None
```

#### 2. Error Handling on Detection

```python
def pausar_por_erro(erro_detectado: str, item_id: str, checkpoint_name: str):
    """
    PARA O RPA COMPLETAMENTE quando erro é detectado

    IMPORTANTE: Esta função PARA a execução do RPA. O robô NÃO continua processando
    outros itens após detectar um erro. O usuário deve:
    1. Resolver o erro manualmente no Oracle
    2. Executar o RPA novamente

    Args:
        erro_detectado: Nome da imagem do erro
        item_id: ID do item sendo processado
        checkpoint_name: Onde o erro foi detectado
    """
    log("")
    log("=" * 70)
    log(f"🚨 ERRO DETECTADO: {erro_detectado}")
    log("=" * 70)
    log(f"📍 Local: {checkpoint_name}")
    log(f"📋 Item ID: {item_id}")
    log("")
    log("⚠️ Modal de erro detectado - verifique os dados antes de continuar")
    log("🛑 RPA PARADO COMPLETAMENTE - Resolva o erro manualmente e execute novamente")
    log("🛑 O ROBÔ NÃO CONTINUARÁ PROCESSANDO OUTROS ITENS")
    log("=" * 70)
    log("")

    # Marcar item com erro específico
    if item_id:
        status_erro = f"Erro: {erro_detectado.replace('.png', '').replace('_', ' ').title()}"
        gsheets.atualizar_status_rpa(
            item_id=item_id,
            status=status_erro,
            tipo_contagem=tipo_contagem,
            tipo_planilha=tipo_planilha,
            robo_id=_robo_id
        )
        log(f"✅ Item marcado como '{status_erro}' para reprocessamento")

    # PARAR RPA COMPLETAMENTE - raise Exception interrompe toda execução
    raise Exception(f"ERRO DETECTADO: {erro_detectado} no checkpoint {checkpoint_name}")
```

#### 3. Integration Points in main_inventario.py

**Checkpoint 1: After Item Entry (New Items Only)**
```python
# Linha ~628 - Após digitar Item
digitar(item_valor, "Item")
log(f"✅ Item preenchido: {item_valor}")

# NOVO: Verificar erro após preencher Item
erro = verificar_erro_modal("after_item", timeout=2)
if erro:
    pausar_por_erro(erro, item_id, "after_item")
```

**Checkpoint 2: After Endereço Entry**
```python
# Linha ~637 - Após digitar Endereço
digitar(endereco, "Endereço")
log(f"✅ Endereço preenchido: {endereco}")

# NOVO: Verificar erro após preencher Endereço
erro = verificar_erro_modal("after_endereco", timeout=2)
if erro:
    pausar_por_erro(erro, item_id, "after_endereco")
```

**Checkpoint 3: After SubInventário Entry**
```python
# Linha ~632 - Após digitar Sub Inventário
digitar(subinventario, "Sub Inventário")
log(f"✅ Sub Inventário preenchido: {subinventario}")

# NOVO: Verificar erro após preencher SubInventário
erro = verificar_erro_modal("after_subinventario", timeout=2)
if erro:
    pausar_por_erro(erro, item_id, "after_subinventario")
```

**Checkpoint 4: After UDM Entry (After TAB)**
```python
# Linha ~641 - Após TAB no UDM
pressionar_tab(1)
log(f"⏭️ UDM (pulado)")

# NOVO: Verificar erro após passar pelo UDM
erro = verificar_erro_modal("after_udm", timeout=2)
if erro:
    pausar_por_erro(erro, item_id, "after_udm")
```

**Checkpoint 5: Before Save (Login Validation - Already Implemented)**
```python
# Linhas 657-701 - Validação de login já existe!
# Apenas renomear para usar nomenclatura de checkpoint
erro = verificar_erro_modal("before_save", timeout=2)  # Deteta login_expirado.png
if erro:
    pausar_por_erro(erro, item_id, "before_save")
```

### Configuration Schema

**config.json additions:**
```json
{
  "erro_detection": {
    "comentario": "Configuração de detecção de erros por checkpoint",
    "timeout_por_checkpoint": 2,
    "confianca_padrao": 0.8,
    "checkpoints": {
      "after_item": [
        "erro_item_inexistente.png"
      ],
      "after_endereco": [
        "erro_endereco_inexistente.png"
      ],
      "after_subinventario": [
        "erro_subinventario_inexistente.png"
      ],
      "after_udm": [
        "erro_udm_inexistente.png"
      ],
      "before_save": [
        "login_expirado.png"
      ]
    }
  }
}
```

### Error Image Requirements

**Error Images (Already Exist in elementos/):**
1. ✅ `erro_item_inexistente.png` - Item not found / doesn't exist
2. ✅ `erro_endereco_inexistente.png` - Address not found / doesn't exist
3. ✅ `erro_subinventario_inexistente.png` - Subinventory not found / doesn't exist
4. ✅ `erro_udm_inexistente.png` - UDM not found / doesn't exist
5. ✅ `login_expirado.png` - Login expired (linha 660 já usa)

**Error Images (Already Exist in elementos/teste/):**
- ✅ Same 5 images with test environment styling

**Image Validation Process (Images Already Exist):**
1. ✅ Images already captured and saved in elementos/ and elementos/teste/
2. Validate detection works: Test with confidence=0.8 in localizar_imagem()
3. If detection fails: Recapture or adjust confidence level in config.json

### Build System Updates

**Inventario.spec modifications:**
```python
datas=[
    ('Logo.png', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('config.json', '.'),
    ('elementos', 'elementos'),
    ('elementos/teste', 'elementos/teste'),  # NEW: Include test images
    ('CredenciaisOracle.json', '.'),
],
```

**BUILD_INVENTARIO.bat validation addition:**
```batch
echo [4/8] Validando imagens de erro...
if not exist "elementos\erro_item_inexistente.png" (
    echo ERRO: elementos\erro_item_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\teste\erro_item_inexistente.png" (
    echo ERRO: elementos\teste\erro_item_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\erro_endereco_inexistente.png" (
    echo ERRO: elementos\erro_endereco_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\erro_subinventario_inexistente.png" (
    echo ERRO: elementos\erro_subinventario_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\erro_udm_inexistente.png" (
    echo ERRO: elementos\erro_udm_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\login_expirado.png" (
    echo ERRO: elementos\login_expirado.png nao encontrado
    goto :erro
)
echo OK - Todas as imagens de erro validadas
```

## Performance Impact Analysis

**Current Performance (per item):**
- Field entry: ~5s
- Save operation: ~8s
- **Total: ~13s per item**

**With Error Detection (5 checkpoints × 2s timeout):**
- Best case (no errors): 5 checkpoints × ~0.3s (image not found fast) = +1.5s
- Worst case (checking all images): 5 checkpoints × 2s = +10s
- **Realistic case**: +2-3s per item (images found within 0.4-0.6s each)

**Updated Performance:**
- **Total: ~15-16s per item (+15% overhead)**
- Trade-off acceptable: Error prevention worth 2-3s overhead
- 100 items: adds 3-5 minutes to batch (acceptable for error prevention)

**Optimization Opportunities:**
- Reduce timeout to 1.5s if testing shows modals appear quickly
- Use higher confidence (0.85) to fail faster on non-matches
- Check most common errors first in checkpoint image list

## Testing Strategy

**Manual Testing Checklist:**

1. **Test Environment Validation (modo_teste=True)**
   - ✅ Verify elementos/teste/ images are used
   - ✅ Trigger test environment errors
   - ✅ Confirm correct detection and pause

2. **Production Environment Validation (modo_teste=False)**
   - ✅ Verify elementos/ images are used
   - ✅ Test with production Oracle instance
   - ✅ Confirm correct detection and pause

3. **Checkpoint Testing (each checkpoint)**
   - ✅ after_item: Trigger item validation error
   - ✅ after_endereco: Trigger address error
   - ✅ after_subinventario: Trigger subinv error
   - ✅ after_udm: Trigger UDM error
   - ✅ before_save: Force login expiration

4. **Error Recovery Testing**
   - ✅ Verify item marked with specific error status
   - ✅ Resolve error manually
   - ✅ Re-run RPA and confirm item reprocessed
   - ✅ Verify item marked "PROCESSO CONCLUIDO" after success

5. **Performance Testing**
   - ✅ Process 10 items without errors
   - ✅ Measure total time vs baseline
   - ✅ Confirm overhead is <3s per item

6. **Build Testing**
   - ✅ Run BUILD_INVENTARIO.bat
   - ✅ Verify error image validation passes
   - ✅ Confirm elementos/teste/ included in dist/
   - ✅ Test executable in test mode and production mode

## Deployment Notes

**Deployment Steps:**

1. **✅ Error Images - ALREADY EXIST**
   - Images already exist in elementos/ and elementos/teste/
   - erro_item_inexistente.png
   - erro_endereco_inexistente.png
   - erro_subinventario_inexistente.png
   - erro_udm_inexistente.png
   - login_expirado.png

2. **Update config.json**
   - Add erro_detection section with checkpoint mappings
   - Use existing image names (erro_*_inexistente.png)
   - Adjust timeouts if needed based on network latency

3. **Update main_inventario.py**
   - Add verificar_erro_modal() and pausar_por_erro() functions
   - Insert checkpoint calls at 4 integration points (after Item, Endereço, SubInventário, UDM)
   - before_save checkpoint already exists (linha 657-701 - login validation)
   - Test in development mode

4. **Update Build System**
   - elementos/teste/ already included in spec (verify)
   - Update BUILD_INVENTARIO.bat validation to check error images
   - Run build and test executable

5. **Document for Users**
   - Update README with error detection feature
   - Document: "RPA will pause if error modals detected"
   - Document: "Items marked with specific error for reprocessing"

6. **Gradual Rollout**
   - Deploy to 1 test machine first
   - Run 1-2 batches with mixed error scenarios
   - Monitor logs for false positives
   - Deploy to all machines after validation

## Risk Mitigation

**Risk 1: False Positives (modal detected when not present)**
- Mitigation: Use confidence=0.8 (current standard)
- Mitigation: Crop error images to modal title only (reduces background matching)
- Recovery: User can resume RPA after checking screen

**Risk 2: False Negatives (modal present but not detected)**
- Mitigation: Modals listed in config.json cover all known error types
- Mitigation: 2s timeout allows slower-loading modals to appear
- Recovery: Save will fail, item marked "Erro - Reprocessar", user investigates

**Risk 3: Performance Degradation**
- Mitigation: Realistic overhead is 2-3s per item (15% increase)
- Mitigation: Timeout tunable in config.json if too slow
- Recovery: Can disable specific checkpoints by removing from config

**Risk 4: Missing Error Images**
- Mitigation: BUILD_INVENTARIO.bat validates images exist before build
- Mitigation: Development testing will identify missing images early
- Recovery: Build fails with clear error message indicating missing image

**Risk 5: Environment Differences (test vs prod modals look different)**
- Mitigation: Separate image sets (elementos/ vs elementos/teste/)
- Mitigation: modo_teste flag automatically selects correct image set
- Recovery: Capture environment-specific images if detection fails

## Conclusion

This implementation plan provides a robust, configuration-driven error detection system that aligns with all applicable constitution principles. The checkpoint-based approach adds minimal overhead (~2-3s per item) while significantly improving data quality and preventing invalid saves. The design leverages existing PyAutoGUI infrastructure and maintains the standalone build requirement through proper resource bundling.

**Ready for Phase 0 Research** to finalize optimal checkpoint timing and error image naming conventions.
