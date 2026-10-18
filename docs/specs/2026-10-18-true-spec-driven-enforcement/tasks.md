# Execution Tasks: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Implemented`

## Phase 2 Implementation Checklist (Completed)

- [x] **Task 1: Implement status normalization, canonical tiers, and path containment in `scripts/spec_checker.py`** (`REQ-002`, `REQ-003`, `REQ-006`)
- [x] **Task 2: Implement `REQ-\d+` traceability and 4-document validation in `scripts/spec_checker.py`** (`REQ-001`, `REQ-003`, `REQ-006`)
- [x] **Task 3: Harden `scripts/spec-gate.py` and expand `hooks.json`** (`REQ-002`, `REQ-004`, `REQ-005`)
- [x] **Task 4: Align `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` contracts** (`REQ-007`)
- [x] **Task 5: Rewrite & expand unit tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py`** (`REQ-008`)
- [x] **Task 6: Run verification suite and record verbatim output in `verification.md`** (`REQ-001`, `REQ-008`)

## Phase 3 Architectural Remediation Checklist (For Delegated Agent)

- [x] **Task 7: Fix terminal-status verification, remove `design.md` bypass, and anchor declared `REQ-\d+` extraction in `scripts/spec_checker.py`** (`REQ-001`, `REQ-003`, `REQ-006`)
  - Implement `extract_declared_requirement_ids(spec_text: str) -> List[str]` using `DECLARED_REQ_LINE_PATTERN` (headings, bullet lead-ins, table cells) with fallback to `extract_requirement_ids(spec_text)` so prose references in `spec.md` do not become false requirement declarations (`AC-001-1`).
  - Remove the undocumented `Governing Specification:.*spec\.md` bypass in `validate_spec_package()` so `design.md` must always reference all declared requirement IDs (`AC-001-2`).
  - Change `if len(parts) < 6:` to `if len(parts) != 6:` in `parse_specs_index()` so rows with `> 6` columns raise `ValueError` (`AC-003-4`).
  - In `verify_active_specification()`, include `VERIFIABLE_TERMINAL_STATUSES = {"completed", "implemented", "done"}` in `target_specs` when `feature_id` is explicitly specified (`AC-006-2`) or when `verify_evidence=True` and no active (`EXECUTION_STATUSES | PLANNING_STATUSES`) specs exist (`AC-006-3`), and automatically set `verify_evidence=True` whenever validating a spec in `VERIFIABLE_TERMINAL_STATUSES` (`AC-001-3`).
- [x] **Task 8: Add mechanical self-approval guard, symlink containment, `cwd` precedence, and tightened runtime path check in `scripts/spec-gate.py`** (`REQ-004`, `REQ-005`)
  - Update workspace root resolution order to `os.environ.get("AGY_ACTIVE_WORKSPACE") or payload.get("cwd") or os.getcwd()` (`AC-004-2.1`).
  - Check lexical vs. resolved target path containment: if `lexical_abs.is_relative_to(workspace_path)` and `not resolved_target.is_relative_to(workspace_path)`, return `{"decision": "deny"}` to block in-workspace symlink escapes (`AC-004-2.3`).
  - Tighten `is_allowed_runtime_artifact_path()` to allow `.gemini/antigravity/brain`, `.gemini/antigravity/scratch`, and `os.environ.get("AGY_RUNTIME_ARTIFACT_DIR")`, removing the blanket `/tmp` and `tempfile.gettempdir()` exemptions (`AC-004-2.4`).
  - Implement `is_unauthorized_status_promotion()` in `scripts/spec-gate.py`: when a file-mutation tool targets `docs/specs/INDEX.md`, deny writes that introduce or promote a feature row into `EXECUTION_STATUSES` (`approved`, `in-progress`, `active`) unless that feature is already in `EXECUTION_STATUSES` in the on-disk `INDEX.md` or `os.environ.get("SPEC_GATE_ALLOW_APPROVAL") == "1"` (`AC-004-4`).
- [x] **Task 9: Clarify fast-path vs. mechanical gate scope in `rules/spec-standard.md` and `skills/spec-standard/SKILL.md`** (`REQ-007`)
  - Update `<scope>` in `rules/spec-standard.md` and Section 1 in `skills/spec-standard/SKILL.md` to clarify that in repositories containing `docs/specs/`, `spec-gate.py` mechanically requires an active `EXECUTION_STATUSES` specification for all workspace file edits outside `docs/specs/` (`AC-007-2`).
- [x] **Task 10: Expand unit tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py`** (`REQ-008`)
  - Update `test_direct_mutation_external_brain_artifact_exemption` in `tests/test_spec_gate.py` to use a `.gemini/antigravity/brain/...` path (matching `AC-004-2.4`).
  - Add unit tests in `tests/test_spec_checker.py` for: (a) `extract_declared_requirement_ids()` ignoring prose mentions, (b) `Governing Specification: spec.md` no longer bypassing `design.md` traceability, (c) `> 6` column rows raising `ValueError` / `corrupt_index`, and (d) `Implemented` / `Completed` specs passing `verify_active_specification()` when `--feature` or `verify_evidence=True` is supplied while still blocking `require_approved=True` when `verify_evidence=False, feature_id=None`.
  - Add unit tests in `tests/test_spec_gate.py` for: (a) blocking self-approval writes to `docs/specs/INDEX.md` while allowing edits to already-approved features or `Draft`/`Planning` rows, and (b) blocking in-workspace symlinks that resolve outside `workspace_root`.
- [x] **Task 11: Clean up `reviews/spec-v1.json` and record fresh Phase 3 verification evidence in `verification.md`** (`REQ-001`, `REQ-008`)
  - Delete `docs/specs/2026-10-18-true-spec-driven-enforcement/reviews/spec-v1.json` (and remove empty `reviews/` directory) (`AC-008-1`).
  - Run `pytest -v` and `python3 scripts/spec_checker.py --workspace . --verify-evidence --json` and record the verbatim outputs in `docs/specs/2026-10-18-true-spec-driven-enforcement/verification.md` (`AC-008-3`).
