# Data Model: Modal Error Detection

**Date**: 2025-12-14
**Purpose**: Define data structures for error detection configuration and runtime state

## Overview

This feature does not involve traditional database entities or API contracts. Instead, it defines configuration schemas and runtime data structures used by the error detection system.

## Configuration Schema

### 1. erro_detection (config.json)

**Purpose**: Configure error detection behavior, timeouts, and checkpoint-to-image mappings

**Schema**:
```json
{
  "erro_detection": {
    "comentario": "Configuração de detecção de erros por checkpoint",
    "wait_before_check": 0.5,
    "timeout_per_check": 1.5,
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

**Field Definitions**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `comentario` | string | No | - | Human-readable description of section |
| `wait_before_check` | float | Yes | 0.5 | Seconds to wait after field entry before checking for modal |
| `timeout_per_check` | float | Yes | 1.5 | Maximum seconds to search for error modal images |
| `confianca_padrao` | float | Yes | 0.8 | Default confidence level for image matching (0.0-1.0) |
| `checkpoints` | object | Yes | - | Map of checkpoint names to error image arrays |
| `checkpoints.<name>` | array[string] | Yes | - | List of error image filenames to check at this checkpoint |

**Validation Rules**:
- `wait_before_check` must be ≥ 0 and ≤ 5.0 seconds
- `timeout_per_check` must be ≥ 0.5 and ≤ 10.0 seconds
- `confianca_padrao` must be between 0.5 and 1.0
- Each checkpoint must have at least one error image
- Image filenames must end with `.png`
- Checkpoint names must match: `after_item`, `after_endereco`, `after_subinventario`, `after_udm`, `before_save`

**Example (Minimal)**:
```json
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

**Example (Advanced - Multiple Errors per Checkpoint)**:
```json
{
  "erro_detection": {
    "wait_before_check": 0.7,
    "timeout_per_check": 2.0,
    "confianca_padrao": 0.85,
    "checkpoints": {
      "after_item": [
        "erro_item_inexistente.png",
        "erro_item_inativo.png",
        "erro_item_bloqueado.png"
      ],
      "after_endereco": [
        "erro_endereco_inexistente.png"
      ],
      "after_subinventario": [
        "erro_subinventario_inexistente.png",
        "erro_subinventario_bloqueado.png"
      ],
      "after_udm": [
        "erro_udm_inexistente.png"
      ],
      "before_save": [
        "login_expirado.png",
        "sessao_expirada.png"
      ]
    }
  }
}
```

---

## Runtime Data Structures

### 2. Checkpoint Definition

**Purpose**: Runtime representation of detection checkpoint

**Structure** (Python):
```python
@dataclass
class Checkpoint:
    """Represents a single error detection checkpoint"""
    name: str                    # Checkpoint identifier (e.g., "after_item")
    error_images: List[str]      # Images to check (e.g., ["erro_item_inexistente.png"])
    wait_before: float           # Seconds to wait before checking
    timeout: float               # Seconds to spend checking for images
    confidence: float            # Image matching confidence (0.0-1.0)

# Example instance
checkpoint_item = Checkpoint(
    name="after_item",
    error_images=["erro_item_inexistente.png"],
    wait_before=0.5,
    timeout=1.5,
    confidence=0.8
)
```

**Usage**:
```python
def executar_checkpoint(checkpoint: Checkpoint, item_id: str) -> Optional[str]:
    """
    Execute error detection at checkpoint

    Returns:
        Nome da imagem de erro detectada ou None
    """
    esperar(checkpoint.wait_before, f"aguardar validação - {checkpoint.name}")

    for imagem_erro in checkpoint.error_images:
        posicao = localizar_imagem(
            imagem_erro,
            confianca=checkpoint.confidence,
            timeout=checkpoint.timeout
        )
        if posicao:
            return imagem_erro

    return None
```

---

### 3. Error Detection Result

**Purpose**: Capture result of error detection check

**Structure** (Python):
```python
@dataclass
class ErrorDetectionResult:
    """Result of error detection at a checkpoint"""
    checkpoint_name: str         # Where check occurred (e.g., "after_item")
    error_detected: bool         # True if modal found
    error_image: Optional[str]   # Filename of detected error (if any)
    detection_time: float        # Seconds spent detecting
    timestamp: datetime          # When check occurred

# Example - Error detected
result_error = ErrorDetectionResult(
    checkpoint_name="after_item",
    error_detected=True,
    error_image="erro_item_inexistente.png",
    detection_time=0.6,
    timestamp=datetime.now()
)

# Example - No error
result_ok = ErrorDetectionResult(
    checkpoint_name="after_endereco",
    error_detected=False,
    error_image=None,
    detection_time=1.5,
    timestamp=datetime.now()
)
```

**Usage**:
```python
def verificar_erro_modal(checkpoint_name: str) -> ErrorDetectionResult:
    """Execute error detection and return structured result"""
    start_time = time.time()

    config_erro = CONFIG.get('erro_detection', {})
    checkpoint_config = config_erro.get('checkpoints', {}).get(checkpoint_name, [])

    # Check for errors
    for imagem_erro in checkpoint_config:
        posicao = localizar_imagem(imagem_erro, ...)
        if posicao:
            return ErrorDetectionResult(
                checkpoint_name=checkpoint_name,
                error_detected=True,
                error_image=imagem_erro,
                detection_time=time.time() - start_time,
                timestamp=datetime.now()
            )

    return ErrorDetectionResult(
        checkpoint_name=checkpoint_name,
        error_detected=False,
        error_image=None,
        detection_time=time.time() - start_time,
        timestamp=datetime.now()
    )
```

---

### 4. Item Processing State

**Purpose**: Track error detection state during item processing

**Structure** (Python):
```python
@dataclass
class ItemProcessingState:
    """Tracks state of item being processed"""
    item_id: str                                  # Item ID from spreadsheet
    etiqueta: str                                 # Etiqueta being processed
    checkpoints_passed: List[str] = field(default_factory=list)  # Completed checkpoints
    checkpoints_failed: Dict[str, str] = field(default_factory=dict)  # Failed checkpoints -> error image
    current_checkpoint: Optional[str] = None      # Currently executing checkpoint
    processing_start: datetime = field(default_factory=datetime.now)
    processing_end: Optional[datetime] = None

# Example - Successful processing
state_success = ItemProcessingState(
    item_id="A123",
    etiqueta="ETQ-001",
    checkpoints_passed=["after_item", "after_endereco", "after_subinventario", "after_udm", "before_save"],
    checkpoints_failed={},
    processing_end=datetime.now()
)

# Example - Failed at checkpoint
state_failed = ItemProcessingState(
    item_id="A124",
    etiqueta="ETQ-002",
    checkpoints_passed=["after_item"],
    checkpoints_failed={"after_endereco": "erro_endereco_inexistente.png"},
    current_checkpoint="after_endereco",
    processing_end=datetime.now()
)
```

**Usage**:
```python
# Track state during item processing
state = ItemProcessingState(item_id=item_id, etiqueta=etiqueta)

# Pass checkpoint
state.checkpoints_passed.append("after_item")
log(f"✅ Checkpoint passed: after_item")

# Fail checkpoint
state.current_checkpoint = "after_endereco"
erro_detectado = verificar_erro_modal("after_endereco")
if erro_detectado:
    state.checkpoints_failed["after_endereco"] = erro_detectado
    pausar_por_erro(erro_detectado, item_id, "after_endereco")
```

---

## Google Sheets Integration

### 5. Status RPA Field Values

**Purpose**: Define valid status values written to "Status RPA" column in Google Sheets

**Status Values** (existing + new):

| Status Value | When Set | Meaning | Reprocessable? |
|--------------|----------|---------|----------------|
| `PROCESSANDO...` | Item processing starts | Item reserved by robot | No (locked) |
| `PROCESSO CONCLUIDO` | Item saved successfully | Processing complete | No |
| `Interrompido - Reprocessar` | User pressed ESC | Manual stop | Yes |
| `Erro - Reprocessar` | Generic error occurred | Unknown error | Yes |
| `Login Oracle Expirado` | before_save checkpoint failed | Session expired | Yes |
| `Erro: Item Inexistente` | after_item checkpoint failed | Item not found error | Yes |
| `Erro: Endereco Inexistente` | after_endereco checkpoint failed | Address not found error | Yes |
| `Erro: Subinventario Inexistente` | after_subinventario checkpoint failed | Subinventory not found error | Yes |
| `Erro: Udm Inexistente` | after_udm checkpoint failed | UDM not found error | Yes |

**Status Format for Error Detection**:
```python
def gerar_status_erro(erro_imagem: str) -> str:
    """
    Convert error image filename to readable status

    Examples:
        erro_item_inexistente.png → "Erro: Item Inexistente"
        erro_endereco_inexistente.png → "Erro: Endereco Inexistente"
        login_expirado.png → "Login Oracle Expirado"
    """
    if "login" in erro_imagem.lower():
        return "Login Oracle Expirado"

    # Remove .png extension and replace underscores
    status = erro_imagem.replace(".png", "").replace("_", " ")

    # Capitalize words
    status_parts = status.split()
    status_formatted = " ".join(word.title() for word in status_parts)

    return f"Erro: {status_formatted.replace('Erro ', '')}"

# Examples:
gerar_status_erro("erro_item_inexistente.png")          # → "Erro: Item Inexistente"
gerar_status_erro("erro_endereco_inexistente.png")     # → "Erro: Endereco Inexistente"
gerar_status_erro("erro_subinventario_inexistente.png") # → "Erro: Subinventario Inexistente"
gerar_status_erro("login_expirado.png")                # → "Login Oracle Expirado"
```

---

## Error Image File Structure

### 6. Image File Metadata

**Purpose**: Define expected structure and metadata for error detection images

**Directory Structure**:
```
rpa_inventario/
├── elementos/                             # Production environment images
│   ├── erro_item_inexistente.png          # ✅ EXISTS
│   ├── erro_endereco_inexistente.png      # ✅ EXISTS
│   ├── erro_subinventario_inexistente.png # ✅ EXISTS
│   ├── erro_udm_inexistente.png           # ✅ EXISTS
│   ├── login_expirado.png                 # ✅ EXISTS
│   └── (other UI element images...)
└── elementos/teste/                       # Test environment images
    ├── erro_item_inexistente.png          # ✅ EXISTS
    ├── erro_endereco_inexistente.png      # ✅ EXISTS
    ├── erro_subinventario_inexistente.png # ✅ EXISTS
    ├── erro_udm_inexistente.png           # ✅ EXISTS
    ├── login_expirado.png                 # ✅ EXISTS
    └── (other UI element images...)
```

**Image Specifications**:

| Attribute | Specification | Rationale |
|-----------|--------------|-----------|
| Format | PNG | Lossless, supports transparency, PyAutoGUI compatible |
| Color Mode | RGB or RGBA | Match screen capture format |
| Recommended Size | 200-600px width | Crop to modal title + first line of text |
| Max File Size | < 500 KB | Faster loading, smaller build size |
| DPI | 96 DPI (Windows standard) | Match screen resolution |
| Confidence Threshold | 0.8 | Balance false positives vs false negatives |

**Image Validation Process (Images Already Captured)**:
1. ✅ Images already exist in elementos/ and elementos/teste/
2. Verify naming matches expected pattern: `erro_{field}_inexistente.png`
3. Test detection: `localizar_imagem("erro_item_inexistente.png", confianca=0.8, timeout=2)`
4. If detection fails: recapture image or adjust confidence in config.json
5. Ensure test and production versions are visually distinct (if environments differ)

---

## State Transitions

### 7. Item Processing State Machine

**States**:
1. **PENDING** - Item in spreadsheet, not yet processed
2. **LOCKED** - Item marked "PROCESSANDO..." (reserved by robot)
3. **PROCESSING** - Robot filling fields, executing checkpoints
4. **ERROR_DETECTED** - Modal detected at checkpoint
5. **COMPLETED** - Item saved, marked "PROCESSO CONCLUIDO"
6. **FAILED** - Item marked with error status for reprocessing

**Transitions**:
```
PENDING → LOCKED
  Trigger: Robot selects item from spreadsheet
  Action: Update Status RPA = "PROCESSANDO..."

LOCKED → PROCESSING
  Trigger: Robot starts filling fields
  Action: Begin checkpoint execution

PROCESSING → ERROR_DETECTED
  Trigger: verificar_erro_modal() returns error image
  Action: Log error, update Status RPA with specific error

PROCESSING → COMPLETED
  Trigger: All checkpoints pass, save successful
  Action: Update Status RPA = "PROCESSO CONCLUIDO"

ERROR_DETECTED → FAILED
  Trigger: pausar_por_erro() called
  Action: Raise exception, stop RPA

PROCESSING → FAILED
  Trigger: Generic exception during processing
  Action: Update Status RPA = "Erro - Reprocessar"

FAILED → PENDING (User Action)
  Trigger: User resolves error, clears Status RPA
  Action: Item available for reprocessing
```

**State Persistence**:
- State stored in Google Sheets "Status RPA" column
- No local state file needed (stateless RPA)
- Robot ID tracked for parallel processing safety

---

## Configuration Validation

### 8. Startup Validation Rules

**Purpose**: Validate config.json error detection section at RPA startup

**Validation Checks**:

```python
def validar_config_erro_detection():
    """Validate erro_detection configuration at startup"""
    erros = []

    config_erro = CONFIG.get('erro_detection', {})

    # Check required fields
    if 'wait_before_check' not in config_erro:
        erros.append("erro_detection.wait_before_check não encontrado")
    elif not (0 <= config_erro['wait_before_check'] <= 5.0):
        erros.append("erro_detection.wait_before_check deve estar entre 0 e 5.0")

    if 'timeout_per_check' not in config_erro:
        erros.append("erro_detection.timeout_per_check não encontrado")
    elif not (0.5 <= config_erro['timeout_per_check'] <= 10.0):
        erros.append("erro_detection.timeout_per_check deve estar entre 0.5 e 10.0")

    if 'confianca_padrao' not in config_erro:
        erros.append("erro_detection.confianca_padrao não encontrado")
    elif not (0.5 <= config_erro['confianca_padrao'] <= 1.0):
        erros.append("erro_detection.confianca_padrao deve estar entre 0.5 e 1.0")

    # Check checkpoints
    checkpoints = config_erro.get('checkpoints', {})
    required_checkpoints = ["after_item", "after_endereco", "after_subinventario", "after_udm", "before_save"]

    for cp in required_checkpoints:
        if cp not in checkpoints:
            erros.append(f"Checkpoint '{cp}' não configurado em erro_detection.checkpoints")
        elif not isinstance(checkpoints[cp], list) or len(checkpoints[cp]) == 0:
            erros.append(f"Checkpoint '{cp}' deve ter pelo menos uma imagem de erro")

    # Check image files exist
    for cp_name, imagens in checkpoints.items():
        for imagem in imagens:
            if _modo_teste:
                caminho = ELEMENTOS_DIR / "teste" / imagem
            else:
                caminho = ELEMENTOS_DIR / imagem

            if not caminho.exists():
                erros.append(f"Imagem de erro não encontrada: {caminho}")

    if erros:
        log("❌ ERRO na configuração de detecção de erros:")
        for erro in erros:
            log(f"   - {erro}")
        raise ValueError(f"Configuração erro_detection inválida: {len(erros)} erros encontrados")
    else:
        log("✅ Configuração erro_detection validada com sucesso")
```

---

## Summary

This data model defines:

1. **Configuration schema** for erro_detection in config.json
2. **Runtime data structures** for checkpoints and detection results
3. **Item processing state tracking** through Google Sheets
4. **Error image file structure** and specifications
5. **State machine** for item processing lifecycle
6. **Validation rules** for configuration

**Key Relationships**:
- Each **Checkpoint** maps to multiple **Error Images**
- Each **Error Image** produces a specific **Status Value** in Google Sheets
- Each **Item** passes through multiple **Checkpoints** during processing
- **Configuration** drives runtime behavior (wait times, timeouts, confidence)

**No Traditional Database/API** - This is a desktop automation system using:
- Google Sheets for persistence (via existing google_sheets_inventario.py)
- config.json for configuration
- File system for error images
- Python data structures for runtime state
