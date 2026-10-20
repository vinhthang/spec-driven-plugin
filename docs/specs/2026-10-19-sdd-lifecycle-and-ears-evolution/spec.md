# Specification: SDD Lifecycle Automation, Checkbox Hash Normalization & EARS Governance

- **Feature ID**: `2026-10-19-sdd-lifecycle-and-ears-evolution`
- **Status**: `Planning`
- **Version**: `1.0.0`
- **Date**: `2026-10-19`

## 1. Problem Statement & Context

Following our comparative research against AWS Kiro, GitHub Spec Kit, and OpenSpec, five lifecycle and usability gaps remain in `spec-driven-plugin`:
1. **Mid-Execution Hash Invalidation (`tasks.md` Checkboxes)**: `compute_spec_package_hash()` in `scripts/semantic_checker.py` hashes raw `tasks.md` text. When Phase 2 subagents mark `- [ ]` as `- [x]` in `tasks.md`, `spec_hash` changes and invalidates `traceability_audit.json` mid-execution.
2. **Zombie Approved Specs & Unchecked Tasks**: Completed features often remain in `Approved` status in `docs/specs/INDEX.md`, allowing subsequent sessions to bypass `spec-gate.py`. Furthermore, there is no mechanical check preventing a feature with unchecked `- [ ]` tasks from being transitioned to `Implemented`/`Completed`, nor a `--close <feature-id>` CLI command.
3. **Manual Scaffolding Ceremony**: Creating a new 5-document specification package requires manually scanning `docs/specs/` for the next available `REQ-NNN` and `ADR-NNN` IDs and making 5 separate file-creation calls instead of a single `--init <feature-id>` command.
4. **Documentation Friction After Spec Closure**: Once all specs in `docs/specs/INDEX.md` are closed (`Implemented`), `spec-gate.py` blocks editing non-code documentation files such as `README.md`, `CHANGELOG.md`, or `docs/*.md`.
5. **Unresolved Ambiguity Markers & EARS Guidance**: Unfinished drafts containing `[NEEDS CLARIFICATION]`, `TODO:`, `TBD:`, or `FIXME:` in `spec.md`, `decisions.md`, or `design.md` are not caught mechanically in `spec_checker.py` before invoking the Opus `traceability-auditor`, and `skills/spec-standard/SKILL.md` lacks EARS (Easy Approach to Requirements Syntax) templates.

---

## 2. Normative Requirements (EARS Notation)

### `REQ-018`: Volatile Checkbox Normalization in `compute_spec_package_hash()`
- **Statement**: WHEN computing the SHA-256 specification hash in `scripts/semantic_checker.py`, THE `compute_spec_package_hash()` function SHALL normalize checked Markdown task items (`- [x]`, `- [X]`, `* [x]`, `+ [x]`) in `tasks.md` to unchecked `- [ ]` items before hashing.
- **Acceptance Criteria**:
  - `AC-018-1`: Toggling task checkboxes between `[ ]` and `[x]`/`[X]` in `tasks.md` produces an identical `spec_hash` and `evidence_hash`.
  - `AC-018-2`: Modifying task descriptions, adding/removing tasks, or changing requirement IDs in `tasks.md` produces a different `spec_hash`.

### `REQ-019`: Task Completion Enforcement & Automated Spec Closure (`--close <feature-id>`)
- **Statement**: WHEN a feature is closed via `spec_checker.py --close <feature-id>` or transitioned to a verifiable terminal status (`Implemented`, `Completed`, `Done`) in `docs/specs/INDEX.md`, THE system SHALL verify that `tasks.md` contains at least one completed `- [x]` task and zero unchecked `- [ ]` tasks, and that `validate_spec_package(pkg_dir, verify_evidence=True)` passes.
- **Acceptance Criteria**:
  - `AC-019-1`: `validate_task_completion(package_dir: Path) -> Tuple[bool, str]` returns `(False, reason)` if `tasks.md` has any unchecked `- [ ]` items or zero `- [x]` items, and `(True, "")` when all tasks are `[x]`.
  - `AC-019-2`: `close_spec_package(workspace_root, feature_id)` (`spec_checker.py --close <feature-id>`) verifies `validate_task_completion(pkg_dir)` and `validate_spec_package(pkg_dir, verify_evidence=True)`, updates `traceability_audit.json`'s `evidence_hash` if needed, and transitions the feature's status to `Implemented` in both `docs/specs/INDEX.md` and `spec.md`.
  - `AC-019-3`: `is_unauthorized_status_promotion()` in `scripts/spec-gate.py` denies transitioning a feature in `docs/specs/INDEX.md` into `VERIFIABLE_TERMINAL_STATUSES` (`implemented`, `completed`, `done`) if `validate_task_completion(pkg_dir)` or `validate_spec_package(pkg_dir, verify_evidence=True)` fails.

### `REQ-020`: Deterministic Spec Package Scaffolder (`--init <feature-id> --title "<Title>"`)
- **Statement**: WHEN `spec_checker.py --init <feature-id> [--title "<Title>"]` is executed, THE system SHALL scan `docs/specs/` for the highest existing `REQ-\d+` and `ADR-\d+` numbers, scaffold `docs/specs/<feature-id>/{spec,decisions,design,tasks}.md` with the next sequential IDs and EARS requirement syntax, and append a `Planning` row to `docs/specs/INDEX.md`.
- **Acceptance Criteria**:
  - `AC-020-1`: `init_spec_package(workspace_root, feature_id, title)` creates `spec.md`, `decisions.md`, `design.md`, and `tasks.md` populated with `REQ-<next>` and `ADR-<next>` and registers the feature as `Planning` in `docs/specs/INDEX.md`.
  - `AC-020-2`: The freshly scaffolded package immediately passes `verify_active_specification(workspace_root, require_approved=False, feature_id=feature_id)` (`--allow-planning`).

### `REQ-021`: Non-Code Documentation Exemption in `spec-gate.py`
- **Statement**: WHEN a file mutation tool targets a non-code documentation Markdown file (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, or `docs/**/*.md` excluding `docs/specs/INDEX.md`), THE `spec-gate.py` hook SHALL allow the edit without requiring an active `Approved` feature specification in `docs/specs/INDEX.md`.
- **Acceptance Criteria**:
  - `AC-021-1`: `is_exempt_documentation_file(resolved_target: Path, target_ws: Path) -> bool` returns `True` for workspace-root `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `.md` files inside `docs/` (while keeping `docs/specs/INDEX.md` status-promotion guards active and keeping `rules/*.md`, `skills/**/*.md`, `agents/*.md`, and all code files gated).

### `REQ-022`: Ambiguity Marker Rejection & EARS Standard Documentation
- **Statement**: WHEN `validate_spec_package()` validates `spec.md`, `decisions.md`, and `design.md`, THE checker SHALL reject documents containing unquoted/unfenced ambiguity markers (`[NEEDS CLARIFICATION]`, `TODO:`, `TBD:`, `FIXME:`), and `skills/spec-standard/SKILL.md` SHALL document EARS requirement templates and the `--init` / `--close` CLI lifecycle.
- **Acceptance Criteria**:
  - `AC-022-1`: `check_ambiguity_markers(content: str, filename: str) -> Optional[str]` strips fenced code blocks and inline backticks and rejects standalone `[NEEDS CLARIFICATION]`, `TODO:`, `TBD:`, or `FIXME:` markers in `spec.md`, `decisions.md`, and `design.md`.
  - `AC-022-2`: `skills/spec-standard/SKILL.md` documents EARS patterns (`WHEN`/`IF`/`WHILE` + `THE system SHALL`) and the `--init` / `--close` CLI commands, and all `.py` files across `scripts/` and `tests/` remain strictly `< 450` lines.
