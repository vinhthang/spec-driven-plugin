# Execution Tasks: Codebase Simplification & Parser Unification

- **Feature ID**: `2026-10-19-simplification-and-deduplication`
- **Status**: `Planning`

## Implementation Checklist

- [x] **Task 1: Extract `parse_specs_index_text()` and `resolve_package_dir()` in `scripts/spec_checker.py`** (`REQ-009`)
  - [x] Extract `parse_specs_index_text(content: str) -> List[Dict[str, str]]` and make `parse_specs_index(index_path)` delegate to it (`AC-009-1`).
  - [x] Extract candidate directory resolution and path containment into `resolve_package_dir(root, specs_dir, feat_id, spec_path_str)` (`AC-009-2`).
- [x] **Task 2: Simplify and harden `scripts/spec-gate.py`** (`REQ-010`, `REQ-011`)
  - [x] Update `is_allowed_runtime_artifact_path()` to verify contiguous `(".gemini", "antigravity", "brain"|"scratch")` path parts (`AC-011-1`, `AC-011-2`).
  - [x] Update `is_unauthorized_status_promotion()` to fail closed when `TargetContent` is unmatched and delegate table parsing to `checker.parse_specs_index_text(projected_text)` (`AC-010-1`, `AC-010-2`).
- [x] **Task 3: Add unit tests and record verification evidence** (`REQ-012`)
  - [x] Add unit tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py` for `parse_specs_index_text()`, unmatched `TargetContent` rejection, partial-cell status replacement rejection, and spoofed brain-substring path rejection (`AC-012-1`).
  - [x] Run `pytest -v` and `python3 scripts/spec_checker.py --workspace . --verify-evidence --json` and record verbatim outputs in `verification.md` (`AC-012-2`).
- [x] **Task 4: Clean up `resolve_package_dir()` single signature in `scripts/spec_checker.py` and sync to `ai-review-plugin`** (`REQ-013`)
  - [x] Remove positional parameter-shifting branch from `resolve_package_dir()` in `scripts/spec_checker.py` (`AC-013-1`) and synchronize byte-for-byte with `ai-review-plugin/scripts/spec_checker.py` (`AC-013-2`).
- [x] **Task 5: Fix `hooks.json` schema and implement `resolve_target_workspace()` & `has_recent_user_approval()` in `scripts/spec-gate.py`** (`REQ-014`)
  - [x] Fix `hooks.json` to use inner `"hooks": [{"type": "command", "command": "/usr/bin/env python3 ./scripts/spec-gate.py", "timeout": 5}]` and resolve workspaces from `payload.get("workspacePaths")` and `resolved_target.parents` (`AC-014-1`).
  - [x] Permit `INDEX.md` promotion to `Approved` when `has_recent_user_approval(payload)` detects explicit user approval in `transcriptPath` (`AC-014-2`).
- [x] **Task 6: Split `tests/test_spec_gate.py` into `test_spec_gate_security.py` and keep all files `< 450` lines** (`REQ-015`)
  - [x] Split security, spoofing, multi-workspace, and `INDEX.md` approval tests into `tests/test_spec_gate_security.py` (`AC-015-1`).
  - [x] Verify all `.py` files in `scripts/` and `tests/` are strictly `< 450` lines and record updated evidence in `verification.md` (`AC-015-2`).
- [x] **Task 7: Implement content-hashed Opus semantic traceability verification (`REQ-016`)**
  - [x] Implement `compute_spec_package_hash()` and `validate_semantic_traceability()` (with CLI `--semantic` flag and `verify_evidence=True` integration) and synchronize to `ai-review-plugin` (`AC-016-1`, `AC-016-2`, `AC-016-3`).
- [x] **Task 8: Add `agents/traceability-auditor.md` and enforce semantic receipt on `Approved` promotion in `spec-gate.py` (`REQ-017`)**
  - [x] Create `agents/traceability-auditor.md` (`model_role: strongest`), enforce `validate_semantic_traceability()` on `INDEX.md` promotion to `Approved` in `spec-gate.py`, reject `flash` model for `traceability-auditor` dispatches, and generate valid `traceability_audit.json` receipts for active specs (`AC-017-1`, `AC-017-2`).

