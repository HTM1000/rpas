<!--
SYNC IMPACT REPORT - Constitution Update

Version Change: 0.0.0 → 1.0.0 (MAJOR - Initial constitution ratification)

Modified Principles:
  - N/A (Initial creation)

Added Sections:
  - Core Principles (I-V): Selenium-First, Configuration-Driven, Standalone Build, GUI Reliability, Error Detection
  - Development Standards: Code quality, testing, and deployment requirements
  - Build & Distribution: PyInstaller packaging standards
  - Governance: Amendment procedure and compliance rules

Removed Sections:
  - N/A (Initial creation)

Templates Requiring Updates:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - Requirements structure supports RPA automation scenarios
  ✅ tasks-template.md - Task organization supports standalone RPA development

Follow-up TODOs:
  - None
-->

# RPA Inventário Constitution

## Core Principles

### I. Selenium-First

All web automation MUST use Selenium WebDriver with intelligent element identification strategies. Selenium provides robust, mature web automation capabilities that are essential for reliable RPA systems.

**Rules:**
- Prefer text-based element identification (buttons, links) over brittle XPath
- Use ID-based selectors when elements have stable IDs
- Fall back to XPath only when text and ID are unavailable
- Always provide descriptive names for click/fill operations in logs
- Include WebDriver Manager for automatic driver management

**Rationale:** Selenium's mature ecosystem and intelligent element selection strategies reduce maintenance burden when web interfaces change. Text-based identification makes automation more resilient to HTML structure changes.

### II. Configuration-Driven

All runtime behavior MUST be controlled through `config.json` with zero hardcoded values in automation logic. Configuration includes URLs, delays, timeouts, and any environment-specific settings.

**Rules:**
- `config.json` MUST contain all URLs, delays, timeouts, and selectors
- Automation code MUST load configuration at startup
- Invalid or missing config values MUST cause immediate startup failure with clear error messages
- Configuration changes MUST NOT require code modifications or rebuilds
- Default values allowed only for non-critical UI preferences

**Rationale:** RPA systems operate in dynamic environments where URLs, timing, and target systems change. Configuration-driven design allows end users to adapt automation to their environment without developer intervention.

### III. Standalone Build (NON-NEGOTIABLE)

Every RPA module MUST build into a standalone executable directory containing ALL dependencies. The executable MUST run on target machines without Python installation or manual dependency management.

**Rules:**
- PyInstaller MUST be used in `onedir` mode (folder with executable + _internal/)
- Build script (`BUILD_INVENTARIO.bat` or similar) MUST validate all resources before build
- All runtime dependencies (images, configs, credentials templates) MUST be included via PyInstaller spec
- Executables MUST bundle Selenium via `collect_all`
- Distribution MUST include entire output folder, never just the .exe
- Build validation MUST confirm executable launches and config.json is accessible

**Rationale:** End users cannot be expected to manage Python environments, virtual environments, or dependency conflicts. Standalone builds ensure zero-friction deployment and predictable runtime environments.

### IV. GUI Reliability

All user interfaces MUST use threading to prevent UI blocking during automation execution. Users MUST have real-time feedback and emergency stop capability at all times.

**Rules:**
- Automation logic MUST run in separate thread from GUI event loop
- GUI MUST remain responsive during automation (no "frozen" windows)
- ESC key MUST provide emergency stop (using `keyboard` library)
- Logs MUST update in real-time in GUI text areas
- GUI MUST display current automation status (idle, running, stopped, error)
- Stop button MUST set shared flag checked by automation thread

**Rationale:** RPA processes can run for extended periods. Blocking GUIs create poor user experience and prevent users from stopping runaway automation. Emergency stop (ESC) is critical for safety.

### V. Error Detection & Visibility

All automation MUST log each action with descriptive names and MUST provide clear error messages with actionable guidance. Silent failures are unacceptable.

**Rules:**
- Every click, fill, navigation action MUST be logged with descriptive name
- Errors MUST include: what failed, why it likely failed, what user should check
- Configuration errors MUST suggest which config.json value to verify
- Element-not-found errors MUST suggest checking URL or site structure
- Logs MUST distinguish: INFO (normal operation), WARNING (recoverable issue), ERROR (failure)
- GUI logs MUST be readable by non-technical users

**Rationale:** RPA systems automate business processes where failures have real consequences. Users must be able to diagnose issues without developer involvement. Clear logging enables self-service troubleshooting.

## Development Standards

### Code Quality

- **Encoding**: All Python files MUST use UTF-8 encoding
- **Naming**: Use descriptive Portuguese function/variable names matching business domain (e.g., `clicar_por_texto`, `preencher_campo`)
- **Comments**: Explain business logic and non-obvious wait conditions, not what code does
- **Error Handling**: Use try-except with specific exceptions; avoid bare `except:`

### Testing Requirements

- **Manual Testing**: MUST test in development mode before building executable
- **Build Validation**: Build script MUST verify executable launches successfully
- **Target Environment**: MUST test on representative target machine (not just dev machine)
- **Chrome Dependency**: Documentation MUST state Google Chrome requirement

### Deployment

- **Documentation**: README MUST document installation, configuration, usage, and dependencies
- **Config Template**: Provide `config.json` with example/placeholder values
- **Changelog**: Track changes in git commit messages or CHANGELOG.md
- **User Guidance**: Include help dialog or instructions in GUI

## Build & Distribution

### PyInstaller Standards

- **Mode**: Use `onedir` mode (never `onefile` for Selenium projects)
- **Spec File**: Maintain `.spec` file for each RPA module
- **Resources**: Explicitly include all data files (images, configs, credential templates) via `datas`
- **Dependencies**: Use `collect_all` for Selenium and related packages
- **Validation**: Build script MUST verify all required resources included
- **Icons**: Provide `.ico` file for Windows executables and `.png` for GUI display

### Distribution Checklist

When distributing builds, verify:
- [ ] Entire `dist/[RPA_NAME]/` folder packaged (not just .exe)
- [ ] `config.json` present and contains valid example values
- [ ] Credential template files included (if applicable)
- [ ] README or help documentation included
- [ ] Chrome installation requirement documented
- [ ] Build tested on clean target machine

## Governance

### Amendment Procedure

1. **Proposal**: Document proposed change with rationale and impact assessment
2. **Review**: Assess impact on existing RPA modules and templates
3. **Approval**: Require explicit approval before adopting breaking changes
4. **Migration**: Update all affected RPA modules and documentation
5. **Version**: Increment constitution version per semantic versioning

### Versioning Rules

- **MAJOR**: Backward-incompatible changes (e.g., removing Selenium requirement, changing build system)
- **MINOR**: New principle added or existing principle materially expanded
- **PATCH**: Clarifications, wording improvements, typo fixes

### Compliance

- All PRs and code reviews MUST verify compliance with constitution principles
- Violations MUST be justified in plan.md Complexity Tracking section
- Constitution supersedes all other coding preferences or conventions
- When constitution conflicts with business requirements, amend constitution (don't bypass it)

**Version**: 1.0.0 | **Ratified**: 2025-10-09 | **Last Amended**: 2025-12-14
