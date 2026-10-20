# Architecture Decision Records (ADR): SDD Lifecycle Automation & EARS Governance

- **Feature ID**: `2026-10-19-sdd-lifecycle-and-ears-evolution`
- **Status**: `Planning`

## `ADR-012`: Normalize Volatile `tasks.md` Checkboxes Before SHA-256 Hashing
- **Context**: `tasks.md` is designed to be updated during Phase 2 execution as subagents mark `- [ ]` tasks as `- [x]`. Hashing raw checkbox states in `compute_spec_package_hash()` caused `spec_hash` in `traceability_audit.json` to become stale as soon as the first task was completed.
- **Decision**: Normalize `- [x]` and `- [X]` list markers in `tasks.md` to `- [ ]` inside `compute_spec_package_hash()` prior to computing the SHA-256 digest.
- **Consequences**: Phase 2 checkbox progress updates do not invalidate the Phase 1 Opus semantic traceability receipt, while any change to task wording, scope, or `REQ-xxx` mapping still invalidates the hash.
- **Addresses**: `REQ-018`

## `ADR-013`: Extract `scripts/spec_lifecycle.py` for `--init`, `--close`, Task Completion & Ambiguity Checks
- **Context**: `scripts/spec_checker.py` is currently 424 lines (26 lines below the 450-line modularity target and 76 lines below the 500-line AST gate). Adding `--init`, `--close`, task checkbox validation, and ambiguity marker detection directly inline in `spec_checker.py` would push it past 450 lines.
- **Decision**: Create `scripts/spec_lifecycle.py` (< 220 lines) housing `init_spec_package()`, `close_spec_package()`, `validate_task_completion()`, and `check_ambiguity_markers()`, and import them into `spec_checker.py` (synchronized byte-for-byte with `ai-review-plugin/scripts/`).
- **Consequences**: Keeps `spec_checker.py`, `semantic_checker.py`, `spec_lifecycle.py`, and `spec-gate.py` each well under 450 lines while adding full CLI lifecycle automation (`--init` and `--close`).
- **Addresses**: `REQ-019`, `REQ-020`, `REQ-022`

## `ADR-014`: Exempt Non-Code Documentation (`README.md`, `CHANGELOG.md`, `docs/**`) & Gate Terminal Closure in `spec-gate.py`
- **Context**: Once `--close` transitions completed specs from `Approved` to `Implemented` (eliminating "Zombie Approved Specs"), editing `README.md` or general documentation under `docs/` would be blocked unless exempted. Conversely, transitioning a spec to `Implemented` in `INDEX.md` must be blocked if `- [ ]` tasks remain unfinished or `verification.md` is incomplete.
- **Decision**:
  1. Add `is_exempt_documentation_file(resolved_target, target_ws)` in `spec-gate.py` to allow edits to `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `docs/**/*.md` (excluding `docs/specs/INDEX.md` promotion/closure checks) without an active `Approved` spec.
  2. In `is_unauthorized_status_promotion()`, verify `validate_task_completion(pkg_dir)` and `validate_spec_package(pkg_dir, verify_evidence=True)` whenever a feature row in `docs/specs/INDEX.md` transitions into `VERIFIABLE_TERMINAL_STATUSES` (`implemented`, `completed`, `done`).
- **Consequences**: Closes the "Zombie Approved Spec" loophole while keeping documentation updates frictionless.
- **Addresses**: `REQ-019`, `REQ-021`
