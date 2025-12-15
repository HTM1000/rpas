# Feature Specification: Modal Error Detection & Login Validation

**Feature Branch**: `001-modal-error-detection`
**Created**: 2025-12-14
**Status**: Draft
**Input**: User description: "quero fazer a seguinte operação! eu adicione novas imagens de erros tanto para o teste quanto para o prod, porém é assim, nem sempre ele vai abrir com aquelas informações mas se aparecer um modal com aquele titulo na tela após passar pelo item, endereço, subinventario e UDM, tem que pausar a aplicação (tem seus modais especificos de acordo com o nome) e além de tudo antes de salvar tem que ter a validação para ver o login, se tiver com erro, tem que pausar também"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Error Modal Detection After Field Entry (Priority: P1)

When the RPA fills in Item, Endereço, SubInventário, and UDM fields, error modals may appear with specific titles. The system must detect these modals and **STOP execution completely** to allow manual intervention.

**Why this priority**: P1 - Critical business logic validation. Error modals indicate data quality issues that require immediate attention to prevent incorrect inventory records. **Stopping execution prevents cascading errors** and ensures data integrity.

**Independent Test**: Can be fully tested by triggering error conditions in test environment (using elementos/teste/ images) and verifying the RPA **stops completely** with appropriate log messages. Delivers immediate value by preventing data errors from being saved.

**Acceptance Scenarios**:

1. **Given** RPA is processing a new item (etiqueta nova) **When** an error modal appears after filling Item field **Then** RPA detects modal by title, logs specific error type, **STOPS execution completely**, and marks item status appropriately
2. **Given** RPA is processing a new item **When** an error modal appears after filling Endereço field **Then** RPA detects modal, **STOPS completely**, marks item with error status, and does NOT process remaining items
3. **Given** RPA is processing a new item **When** an error modal appears after filling SubInventário field **Then** RPA detects modal, **STOPS completely**, and logs subinventory validation error
4. **Given** RPA is processing a new item **When** an error modal appears after filling UDM field **Then** RPA detects modal, **STOPS completely**, and logs UDM validation error
5. **Given** RPA completes field entry without errors **When** no modal is detected **Then** RPA continues to save operation normally

---

### User Story 2 - Pre-Save Login Validation (Priority: P1)

Before clicking the Salvar button, the system must verify the Oracle login session is still active. If login has expired, the RPA must **STOP completely** and prevent attempted saves with invalid session.

**Why this priority**: P1 - Prevents data loss and incomplete transactions. Login expiration during long-running processes can cause silent failures. **Stopping execution** ensures data integrity and prevents corrupted records.

**Independent Test**: Can be tested by forcing login expiration (waiting for session timeout) and verifying RPA detects the login screen before attempting save and **stops completely**. Delivers value by preventing failed save attempts and data loss.

**Acceptance Scenarios**:

1. **Given** RPA has filled all fields for an item **When** login validation detects active session **Then** RPA proceeds to click Salvar button
2. **Given** RPA has filled all fields for an item **When** login validation detects expired session (login_expirado.png) **Then** RPA **STOPS COMPLETELY**, logs "Login Oracle Expirado", marks item for reprocessing, and does NOT continue to next item
3. **Given** login expires during batch processing **When** pre-save validation runs **Then** RPA **STOPS IMMEDIATELY** before saving invalid data and provides clear instructions to re-login

---

### User Story 3 - Environment-Specific Error Images (Priority: P2)

The system must support separate error detection images for test environment (elementos/teste/) and production environment (elementos/), allowing different error modal appearances between environments.

**Why this priority**: P2 - Enables testing without affecting production. Test and production Oracle systems may have different UI styling or error message formats.

**Independent Test**: Can be tested by running RPA in modo_teste=True with test-specific error images and verifying correct image paths are used. Delivers value by enabling safe testing of error handling logic.

**Acceptance Scenarios**:

1. **Given** RPA is running with modo_teste=True **When** error detection executes **Then** images are loaded from elementos/teste/ directory
2. **Given** RPA is running with modo_teste=False (production) **When** error detection executes **Then** images are loaded from elementos/ directory
3. **Given** error image exists in test directory but not production **When** running in test mode **Then** test-specific error is detected correctly

---

### Edge Cases

- What happens when modal appears but doesn't match any known error images?
  - Log "Modal desconhecido detectado" and pause for manual review
- What happens when login expires between validation check and save click?
  - Existing error handling will catch failed save; item marked for reprocessing
- What happens when error modal disappears before RPA can react?
  - Short timeout (2-3s) ensures modals are detected; if missed, subsequent save will likely fail and trigger error handling
- What happens when multiple error modals appear sequentially?
  - Detect and pause on first modal; user resolves before resuming
- What happens when network latency delays modal appearance?
  - Configurable timeout in config.json allows adjustment for slower environments

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST detect error modals by title after filling Item, Endereço, SubInventário, and UDM fields
- **FR-002**: System MUST support environment-specific error images (elementos/ for prod, elementos/teste/ for test)
- **FR-003**: System MUST **STOP execution completely** when error modal is detected (no continuation to next item)
- **FR-004**: System MUST log specific error type based on modal title detected
- **FR-005**: System MUST validate login status before clicking Salvar button
- **FR-006**: System MUST **STOP execution completely** if login expiration is detected (login_expirado.png)
- **FR-007**: System MUST mark items appropriately when stopped due to errors (status: error type or "Login Oracle Expirado")
- **FR-008**: System MUST check for error modals at specific checkpoints: after Item entry, after Endereço entry, after SubInventário entry, after UDM entry
- **FR-009**: System MUST use configurable timeouts for modal detection (not all modals appear immediately)
- **FR-010**: System MUST provide clear log messages indicating which modal/error was detected and at which checkpoint
- **FR-011**: System MUST raise Exception to stop RPA when any error is detected (not just log and continue)

### Configuration Requirements

- **CR-001**: config.json MUST include error detection configuration section with timeout values
- **CR-002**: Error images MUST be named descriptively to indicate error type (e.g., erro_item_invalido.png, erro_endereco.png)
- **CR-003**: config.json MUST specify confidence levels for error modal detection (default: 0.8)

### Key Entities *(include if feature involves data)*

- **Error Modal**: Visual element with specific title that appears on screen when validation fails
  - Attributes: title text, image file name, detection checkpoint (after which field), action (pause RPA)
  - Relationships: Detected at specific checkpoints in item processing flow

- **Detection Checkpoint**: Specific point in automation flow where error modal detection occurs
  - Attributes: checkpoint name (after_item, after_endereco, after_subinventario, after_udm, before_save), list of error images to check
  - Relationships: Each checkpoint maps to one or more potential error modals

- **Login Validation**: Pre-save check to verify Oracle session is active
  - Attributes: validation image (login_expirado.png), timeout, action on detection (pause and mark item)
  - Relationships: Executed before every save operation

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: RPA successfully detects and pauses on error modals in 100% of test cases where modals are triggered
- **SC-002**: RPA prevents saving data when login has expired in 100% of test cases
- **SC-003**: Error detection adds less than 3 seconds total overhead to item processing time (5 checkpoints × ~0.5s each)
- **SC-004**: Users can identify exact error type and location from log messages without examining screenshots
- **SC-005**: Test environment (modo_teste=True) uses test-specific error images without code changes
- **SC-006**: Items paused due to errors are correctly marked for reprocessing after manual intervention
