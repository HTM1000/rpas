---

description: "Task list for Modal Error Detection & Login Validation implementation"
---

# Tasks: Modal Error Detection & Login Validation

**Input**: Design documents from `/specs/001-modal-error-detection/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, research.md

**Tests**: Not requested in specification - manual testing only

**Organization**: Tasks organized by user story to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project root**: `D:\www\rpas\rpa_inventario\`
- **Main automation**: `main_inventario.py`
- **Configuration**: `config.json`
- **Error images**: `elementos/` (prod), `elementos/teste/` (test)
- **Build**: `Inventario.spec`, `BUILD_INVENTARIO.bat`

---

## Phase 1: Setup (Configuration)

**Purpose**: Add error detection configuration to config.json

- [X] T001 Add erro_detection section to config.json with checkpoints mapping

**Implementation Details for T001**:
```json
Add to config.json:
{
  "erro_detection": {
    "wait_before_check": 0.5,
    "timeout_per_check": 1.5,
    "confianca_padrao": 0.8,
    "checkpoints": {
      "after_item": ["erro_item_inexistente.png"],
      "after_endereco": ["erro_endereco_inexistente.png"],
      "after_subinventario": ["erro_subinventario_inexistente.png"],
      "after_udm": ["erro_udm_inexistente.png"],
      "before_save": ["login_expirado.png"]
    }
  }
}
```

---

## Phase 2: Foundational (Core Error Detection Functions)

**Purpose**: Implement shared error detection functions used by all checkpoints

**⚠️ CRITICAL**: This phase MUST be complete before implementing any user story. All checkpoints depend on these functions.

- [X] T002 [P] Implement verificar_erro_modal() function in main_inventario.py (after line 251, before main())
- [X] T003 Implement pausar_por_erro() function in main_inventario.py (after verificar_erro_modal())
- [X] T004 Implement gerar_status_erro() helper function in main_inventario.py (after pausar_por_erro())

**Implementation Details for T002**:
```python
def verificar_erro_modal(checkpoint_name: str) -> Optional[str]:
    """
    Verifica se um modal de erro apareceu na tela

    Args:
        checkpoint_name: Nome do checkpoint (after_item, after_endereco, etc.)

    Returns:
        Nome da imagem do erro detectado ou None
    """
    config_erro = CONFIG.get('erro_detection', {})
    imagens_erro = config_erro.get('checkpoints', {}).get(checkpoint_name, [])
    confianca = config_erro.get('confianca_padrao', 0.8)
    timeout = config_erro.get('timeout_per_check', 1.5)

    log(f"🔍 Checkpoint '{checkpoint_name}': verificando {len(imagens_erro)} erros possíveis...")

    for imagem_erro in imagens_erro:
        posicao = localizar_imagem(imagem_erro, confianca=confianca, timeout=timeout)
        if posicao:
            log(f"🚨 Erro detectado: {imagem_erro}")
            return imagem_erro

    log(f"✅ Checkpoint '{checkpoint_name}': nenhum erro detectado")
    return None
```

**Implementation Details for T003**:
```python
def pausar_por_erro(erro_detectado: str, item_id: str, checkpoint_name: str):
    """
    PARA O RPA COMPLETAMENTE quando erro é detectado

    IMPORTANTE: Esta função PARA a execução do RPA completamente.
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
        status_erro = gerar_status_erro(erro_detectado)
        import google_sheets_inventario as gsheets
        gsheets.atualizar_status_rpa(
            item_id=item_id,
            status=status_erro,
            tipo_contagem=tipo_contagem,
            tipo_planilha=tipo_planilha,
            robo_id=_robo_id
        )
        log(f"✅ Item marcado como '{status_erro}' para reprocessamento")

    # PARAR RPA COMPLETAMENTE
    raise Exception(f"ERRO DETECTADO: {erro_detectado} no checkpoint {checkpoint_name}")
```

**Implementation Details for T004**:
```python
def gerar_status_erro(erro_imagem: str) -> str:
    """
    Converte nome da imagem de erro para status legível

    Examples:
        erro_item_inexistente.png → "Erro: Item Inexistente"
        login_expirado.png → "Login Oracle Expirado"
    """
    if "login" in erro_imagem.lower():
        return "Login Oracle Expirado"

    # Remove .png e substitui underscores
    status = erro_imagem.replace(".png", "").replace("_", " ")

    # Capitaliza palavras
    status_parts = status.split()
    status_formatted = " ".join(word.title() for word in status_parts)

    return f"Erro: {status_formatted.replace('Erro ', '')}"
```

**Checkpoint**: Foundation ready - user story implementation can begin in parallel

---

## Phase 3: User Story 1 - Error Modal Detection After Field Entry (Priority: P1) 🎯 MVP

**Goal**: Detect error modals after filling Item, Endereço, SubInventário, and UDM fields and STOP RPA execution completely

**Independent Test**:
1. Run RPA in modo_teste=True
2. Trigger error condition for Item field (enter invalid item code)
3. Verify RPA detects erro_item_inexistente.png
4. Verify RPA stops execution with log "🛑 RPA PARADO COMPLETAMENTE"
5. Verify item marked in Google Sheets with "Erro: Item Inexistente"
6. Repeat for Endereço, SubInventário, and UDM checkpoints

### Implementation for User Story 1

- [X] T005 [US1] Add checkpoint after Item field entry in main_inventario.py (~line 628)
- [X] T006 [US1] Add checkpoint after Endereço field entry in main_inventario.py (~line 637)
- [X] T007 [US1] Add checkpoint after SubInventário field entry in main_inventario.py (~line 632)
- [X] T008 [US1] Add checkpoint after UDM TAB in main_inventario.py (~line 641)

**Implementation Details for T005**:
```python
# After line 628 (after digitar Item)
digitar(item_valor, "Item")
log(f"✅ Item preenchido: {item_valor}")

# TAB para próximo campo e aguardar validação
pressionar_tab(1)
esperar(0.5, "aguardar validação do campo Item")

# NOVO: Verificar erro após preencher Item
erro = verificar_erro_modal("after_item")
if erro:
    pausar_por_erro(erro, item_id, "after_item")
```

**Implementation Details for T006**:
```python
# After line 637 (after digitar Endereço)
digitar(endereco, "Endereço")
log(f"✅ Endereço preenchido: {endereco}")

# TAB para próximo campo e aguardar validação
pressionar_tab(1)
esperar(0.5, "aguardar validação do campo Endereço")

# NOVO: Verificar erro após preencher Endereço
erro = verificar_erro_modal("after_endereco")
if erro:
    pausar_por_erro(erro, item_id, "after_endereco")
```

**Implementation Details for T007**:
```python
# After line 632 (after digitar Sub Inventário)
digitar(subinventario, "Sub Inventário")
log(f"✅ Sub Inventário preenchido: {subinventario}")

# TAB para próximo campo e aguardar validação
pressionar_tab(1)
esperar(0.5, "aguardar validação do campo SubInventário")

# NOVO: Verificar erro após preencher SubInventário
erro = verificar_erro_modal("after_subinventario")
if erro:
    pausar_por_erro(erro, item_id, "after_subinventario")
```

**Implementation Details for T008**:
```python
# After line 641 (after TAB no UDM)
pressionar_tab(1)
log(f"⏭️ UDM (pulado)")

# Aguardar validação do UDM
esperar(0.5, "aguardar validação UDM")

# NOVO: Verificar erro após passar pelo UDM
erro = verificar_erro_modal("after_udm")
if erro:
    pausar_por_erro(erro, item_id, "after_udm")
```

**Checkpoint**: User Story 1 should now detect all field entry errors and stop RPA completely

---

## Phase 4: User Story 2 - Pre-Save Login Validation (Priority: P1)

**Goal**: Validate Oracle login session before saving and STOP RPA if expired

**Independent Test**:
1. Run RPA normally
2. Wait for Oracle session to expire (or force expiration)
3. RPA fills fields for an item
4. Before clicking Salvar, RPA detects login_expirado.png
5. Verify RPA stops with log "🛑 RPA PARADO COMPLETAMENTE"
6. Verify item marked "Login Oracle Expirado"

### Implementation for User Story 2

- [X] T009 [US2] Refactor existing login validation (lines 657-701) to use verificar_erro_modal() and pausar_por_erro()

**Implementation Details for T009**:

Replace existing login validation code (lines 657-701) with:

```python
# 4.3: Validação de Login Expirado
try:
    log(f"[{index}/{total_itens}] 🔍 Verificando se login do Oracle expirou...")

    # REFATORADO: Usar função verificar_erro_modal
    erro = verificar_erro_modal("before_save")

    if erro:
        # REFATORADO: Usar função pausar_por_erro
        pausar_por_erro(erro, item_id, "before_save")
    else:
        log(f"✅ Login OK - Continuando com salvamento")

except Exception as e:
    # Se for erro de login expirado ou outro erro detectado, re-lançar
    if "ERRO DETECTADO" in str(e) or "LOGIN DO ORACLE EXPIRADO" in str(e):
        raise
    # Outros erros na verificação - apenas avisar e continuar
    log(f"⚠️ Erro ao verificar login expirado: {e}")
    log(f"   Continuando mesmo assim...")
```

**Checkpoint**: User Story 2 now validates login before save using unified error detection

---

## Phase 5: User Story 3 - Environment-Specific Error Images (Priority: P2)

**Goal**: Support separate error images for test (elementos/teste/) and production (elementos/)

**Independent Test**:
1. Run RPA with modo_teste=True
2. Verify logs show images loaded from elementos/teste/
3. Trigger error and verify test image detected
4. Run RPA with modo_teste=False
5. Verify logs show images loaded from elementos/
6. Trigger error and verify prod image detected

### Implementation for User Story 3

- [ ] T010 [US3] Verify localizar_imagem() respects _modo_teste flag for image path selection

**Implementation Details for T010**:

**Verification Steps** (no code changes needed - feature already exists):

1. Check main_inventario.py lines 94-98:
   ```python
   # Se modo teste estiver ativo, buscar em elementos/teste/
   if _modo_teste:
       caminho_imagem = ELEMENTOS_DIR / "teste" / nome_imagem
   else:
       caminho_imagem = ELEMENTOS_DIR / nome_imagem
   ```

2. Verify error images exist in both locations:
   - elementos/erro_item_inexistente.png ✅
   - elementos/erro_endereco_inexistente.png ✅
   - elementos/erro_subinventario_inexistente.png ✅
   - elementos/erro_udm_inexistente.png ✅
   - elementos/login_expirado.png ✅
   - elementos/teste/erro_item_inexistente.png ✅
   - elementos/teste/erro_endereco_inexistente.png ✅
   - elementos/teste/erro_subinventario_inexistente.png ✅
   - elementos/teste/erro_udm_inexistente.png ✅
   - elementos/teste/login_expirado.png ✅

3. Test both modes:
   ```python
   # Test mode
   main(inventario="TEST", modo_teste=True)
   # Verify logs: "🔍 Procurando imagem [TESTE]: ..."

   # Production mode
   main(inventario="PROD", modo_teste=False)
   # Verify logs without [TESTE] marker
   ```

**Checkpoint**: Environment-specific images working (feature already implemented, just verified)

---

## Phase 6: Build System Updates

**Purpose**: Ensure error images are validated during build and included in executable

- [ ] T011 [P] Update Inventario.spec to explicitly include elementos/teste/ in datas
- [ ] T012 Update BUILD_INVENTARIO.bat to validate all error images exist before build

**Implementation Details for T011**:

Verify/update Inventario.spec:
```python
datas=[
    ('Logo.png', '.'),
    ('Tecumseh.png', '.'),
    ('Topo.png', '.'),
    ('config.json', '.'),
    ('elementos', 'elementos'),           # Already includes subdirectories
    # elementos/teste/ is automatically included with elementos/
    ('CredenciaisOracle.json', '.'),
],
```

If elementos/teste/ is not being included, add explicitly:
```python
('elementos/teste', 'elementos/teste'),
```

**Implementation Details for T012**:

Add to BUILD_INVENTARIO.bat after image validation section:

```batch
echo [4/8] Validando imagens de erro...

REM Verificar imagens de erro em elementos/
if not exist "elementos\erro_item_inexistente.png" (
    echo ERRO: elementos\erro_item_inexistente.png nao encontrado
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

REM Verificar imagens de erro em elementos/teste/
if not exist "elementos\teste\erro_item_inexistente.png" (
    echo ERRO: elementos\teste\erro_item_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\teste\erro_endereco_inexistente.png" (
    echo ERRO: elementos\teste\erro_endereco_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\teste\erro_subinventario_inexistente.png" (
    echo ERRO: elementos\teste\erro_subinventario_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\teste\erro_udm_inexistente.png" (
    echo ERRO: elementos\teste\erro_udm_inexistente.png nao encontrado
    goto :erro
)
if not exist "elementos\teste\login_expirado.png" (
    echo ERRO: elementos\teste\login_expirado.png nao encontrado
    goto :erro
)

echo OK - Todas as imagens de erro validadas
```

---

## Phase 7: Polish & Testing

**Purpose**: Final validation and documentation

- [ ] T013 [P] Test error detection in modo_teste=True with all 5 checkpoints
- [ ] T014 [P] Test error detection in production mode with real Oracle errors
- [ ] T015 [P] Validate performance overhead is <3s per item
- [ ] T016 Update README.md with error detection feature documentation

**Implementation Details for T013**:

Manual test checklist:
1. Set modo_teste=True in RPA_Inventario_GUI.py
2. Run RPA with test inventory
3. For each checkpoint:
   - Trigger error condition
   - Verify erro_*_inexistente.png detected
   - Verify RPA stops completely
   - Verify item marked with correct status
   - Verify log shows "🛑 RPA PARADO COMPLETAMENTE"

**Implementation Details for T014**:

Manual test checklist:
1. Set modo_teste=False
2. Run RPA with production Oracle
3. Test each checkpoint with real invalid data:
   - Invalid Item code → erro_item_inexistente.png
   - Invalid Endereço → erro_endereco_inexistente.png
   - Invalid SubInventário → erro_subinventario_inexistente.png
   - Invalid UDM → erro_udm_inexistente.png (if possible)
   - Expired login → login_expirado.png (wait for timeout)

**Implementation Details for T015**:

Performance testing:
1. Measure baseline: Process 10 items without errors
2. Record total time: X seconds
3. Average per item: X/10 = baseline
4. Verify overhead: Should be ~2-3s per item
5. If >3s: Reduce timeout_per_check in config.json

**Implementation Details for T016**:

Add to README.md:

```markdown
## Error Detection

O RPA Inventário detecta automaticamente erros modais após preencher campos e **PARA completamente** quando erro é detectado.

### Erros Detectados

- **Item Inexistente**: Após preencher campo Item
- **Endereço Inexistente**: Após preencher campo Endereço
- **SubInventário Inexistente**: Após preencher campo SubInventário
- **UDM Inexistente**: Após passar pelo campo UDM
- **Login Expirado**: Antes de clicar Salvar

### Comportamento ao Detectar Erro

1. RPA detecta modal de erro pela imagem
2. Loga erro específico no console
3. Marca item na planilha com status do erro
4. **PARA execução completamente**
5. Usuário deve resolver erro manualmente
6. Executar RPA novamente para continuar

### Configuração

A detecção de erros é configurada em `config.json`:

\`\`\`json
{
  "erro_detection": {
    "wait_before_check": 0.5,
    "timeout_per_check": 1.5,
    "confianca_padrao": 0.8,
    "checkpoints": {
      "after_item": ["erro_item_inexistente.png"],
      "after_endereco": ["erro_endereco_inexistente.png"],
      "after_subinventario": ["erro_subinventario_inexistente.png"],
      "after_udm": ["erro_udm_inexistente.png"],
      "before_save": ["login_expirado.png"]
    }
  }
}
\`\`\`

### Imagens de Erro

As imagens de erro estão em:
- **Produção**: `elementos/erro_*.png`
- **Teste**: `elementos/teste/erro_*.png`

O RPA seleciona automaticamente as imagens corretas baseado no modo de execução.
```

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001 config) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T002, T003, T004) completion
- **User Story 2 (Phase 4)**: Depends on Foundational (T002, T003, T004) completion - can run parallel with US1
- **User Story 3 (Phase 5)**: Verification only - can run parallel with US1/US2
- **Build System (Phase 6)**: Can run parallel with user stories
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Independent - requires only Foundational phase
- **User Story 2 (P1)**: Independent - requires only Foundational phase
- **User Story 3 (P2)**: Independent - verification of existing feature

### Critical Path

```
T001 (config)
  → T002, T003, T004 (foundational functions)
    → T005, T006, T007, T008 (US1 checkpoints)
    → T009 (US2 login validation)
    → T010 (US3 verification)
  → T011, T012 (build system - parallel)
  → T013, T014, T015, T016 (testing & docs)
```

### Parallel Opportunities

**After Foundational Phase**:
```bash
# All user stories can start in parallel
Task: T005, T006, T007, T008 (US1 - all checkpoints independent)
Task: T009 (US2 - independent of US1)
Task: T010 (US3 - independent verification)
Task: T011, T012 (Build system updates)
```

**Testing Phase**:
```bash
# All testing tasks parallel
Task: T013 (Test mode testing)
Task: T014 (Production testing)
Task: T015 (Performance testing)
Task: T016 (Documentation)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002-T004) - CRITICAL
3. Complete Phase 3: User Story 1 (T005-T008)
4. **STOP and VALIDATE**: Test all 4 checkpoints detect errors and stop RPA
5. Deploy/demo if ready

**This gives you**: Complete error detection for all field entry errors with RPA stopping behavior

### Full Implementation

1. Setup + Foundational → Foundation ready
2. Add User Story 1 (T005-T008) → Test independently → MVP ready!
3. Add User Story 2 (T009) → Test independently → Login validation added
4. Add User Story 3 (T010) → Verify → Environment support confirmed
5. Add Build System (T011-T012) → Build validation
6. Add Polish (T013-T016) → Production ready

### Quick Start (Minimum Implementation)

If you need to deploy quickly:

1. T001 - Add config
2. T002, T003 - Add core functions
3. T005 - Add Item checkpoint only
4. Test with invalid Item → RPA stops

This gives you **immediate value** with Item error detection while you implement the rest.

---

## Notes

- Total tasks: 16
- User Story 1: 4 tasks (T005-T008) - field entry error detection
- User Story 2: 1 task (T009) - login validation refactor
- User Story 3: 1 task (T010) - verification only
- Foundational: 3 tasks (T002-T004) - BLOCKING for all stories
- Setup: 1 task (T001)
- Build: 2 tasks (T011-T012)
- Polish: 4 tasks (T013-T016)

**Key Success Criteria**:
- ✅ RPA stops completely when any error detected (not just logs and continues)
- ✅ Error images already exist in elementos/ and elementos/teste/
- ✅ All 5 checkpoints implemented (Item, Endereço, SubInventário, UDM, Login)
- ✅ Items marked with specific error status in Google Sheets
- ✅ Performance overhead <3s per item
- ✅ Works in both test and production modes

**Remember**: Each user story can be implemented and tested independently after Foundational phase is complete!
