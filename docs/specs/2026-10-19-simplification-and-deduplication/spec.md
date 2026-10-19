# Specification: Codebase Simplification, Parser Unification & Edge-Case Hardening

- **Feature ID**: `2026-10-19-simplification-and-deduplication`
- **Status**: `Approved`
- **Version**: `1.0.0`
- **Date**: `2026-10-19`

## 1. Problem Statement & Context

Following the self-review in [`docs/specs/SELF_REVIEW.md`](../SELF_REVIEW.md), three maintainability and security issues remain in `spec-driven-plugin`:
1. `verify_active_specification()` in `scripts/spec_checker.py` is 238 lines long (`spec_checker.py` is 489 lines, 11 lines below the 500-line AST gate threshold) because candidate directory resolution is inlined inside the validation loop.
2. `scripts/spec-gate.py` duplicates `INDEX.md` Markdown table parsing logic inside `is_unauthorized_status_promotion()` instead of sharing `spec_checker.py`'s parser, and does not reject unmatched `TargetContent` or partial-row status replacements.
3. `is_allowed_runtime_artifact_path()` in `scripts/spec-gate.py` uses raw string substring matching (`".gemini/antigravity/brain" in target_str`), which can match spoofed path segments outside the user's `.gemini/antigravity/` directory tree.

---

## 2. Normative Requirements

### `REQ-009`: Shared Index Text Parser & Modular Package Directory Resolution
- **Statement**: `scripts/spec_checker.py` MUST expose a reusable `parse_specs_index_text(content: str) -> List[Dict[str, str]]` function and extract candidate package directory resolution into `resolve_package_dir()`, keeping `spec_checker.py` under 450 lines.
- **Acceptance Criteria**:
  - `AC-009-1`: `parse_specs_index_text(content: str)` parses 6-column Markdown tables with escaped-pipe (`\|`) support and raises `ValueError` on malformed rows (`len(parts) != 6`); `parse_specs_index(index_path)` delegates to `parse_specs_index_text()`.
  - `AC-009-2`: `resolve_package_dir(root: Path, specs_dir: Path, feat_id: str, spec_path_str: str)` encapsulates path traversal checks and workspace containment (`is_relative_to(root)`), reducing `verify_active_specification()` to under 140 lines.

### `REQ-010`: Unified Self-Approval Table Parsing & Partial-Edit Rejection in `spec-gate.py`
- **Statement**: `is_unauthorized_status_promotion()` in `scripts/spec-gate.py` MUST reuse `checker.parse_specs_index_text()` and fail closed when `TargetContent` does not match on-disk `INDEX.md` or when a partial-row replacement introduces an execution status token.
- **Acceptance Criteria**:
  - `AC-010-1`: If `"TargetContent"` is present in tool arguments and `TargetContent` is empty or not found in the existing `INDEX.md` content, `is_unauthorized_status_promotion()` returns `True` (unauthorized) with a diagnostic reason.
  - `AC-010-2`: `is_unauthorized_status_promotion()` parses `projected_text` via `checker.parse_specs_index_text(projected_text)` (eliminating duplicate row-splitting code in `spec-gate.py`) and also rejects any raw `ReplacementContent` fragment that contains an `EXECUTION_STATUSES` token (`approved`, `in-progress`, `active`) unless all resulting execution-authorized features were already in `EXECUTION_STATUSES` on disk.

### `REQ-011`: Component-Aware Runtime Artifact Path Validation
- **Statement**: `is_allowed_runtime_artifact_path(target_path: Path)` in `scripts/spec-gate.py` MUST verify contiguous path parts `(".gemini", "antigravity", "brain")` or `(".gemini", "antigravity", "scratch")` (or containment within `AGY_RUNTIME_ARTIFACT_DIR`) rather than raw substring matching.
- **Acceptance Criteria**:
  - `AC-011-1`: Paths with contiguous path components `(".gemini", "antigravity", "brain")` or `(".gemini", "antigravity", "scratch")` (or relative to `AGY_RUNTIME_ARTIFACT_DIR`) return `True`.
  - `AC-011-2`: Spoofed paths that only match as substrings (e.g. `/tmp/fake.gemini/antigravity/brain_spoof/file.py`) return `False`.

### `REQ-012`: Regression & Edge-Case Unit Tests
- **Statement**: `tests/test_spec_checker.py` and `tests/test_spec_gate.py` MUST test `parse_specs_index_text()`, partial-cell status replacement rejection, unmatched `TargetContent` rejection, and spoofed brain-substring path rejection.
- **Acceptance Criteria**:
  - `AC-012-1`: All unit tests in `pytest -v` pass with 0 failures.
  - `AC-012-2`: `python3 scripts/spec_checker.py --workspace . --verify-evidence --json` passes with exit code `0`.

### `REQ-013`: Single-Signature `resolve_package_dir()` Without Parameter Shifting
- **Statement**: `resolve_package_dir(spec: Dict[str, str], root: Path, specs_dir: Optional[Path] = None) -> Tuple[Optional[Path], Optional[str]]` in `scripts/spec_checker.py` MUST use a single explicit signature without overloaded positional parameter shifting, and remain 100% byte-identical across `spec-driven-plugin` and `ai-review-plugin`.
- **Acceptance Criteria**:
  - `AC-013-1`: `resolve_package_dir(spec, root, specs_dir)` accepts a `spec` dictionary (`feature_id`, `spec_path`), `root: Path`, and optional `specs_dir: Path`, removing the `if isinstance(spec, dict): ... else: ...` parameter-shifting branch.
  - `AC-013-2`: `scripts/spec_checker.py` in `spec-driven-plugin` and `ai-review-plugin` are byte-for-byte identical.

### `REQ-014`: Valid `hooks.json` Schema, `workspacePaths` Resolution & Transcript-Backed Approval in `spec-gate.py`
- **Statement**: `hooks.json` MUST conform to Antigravity's inner `"hooks": [{"type": "command", "command": "/usr/bin/env python3 ./scripts/spec-gate.py", "timeout": 5}]` schema, and `scripts/spec-gate.py` MUST resolve the governing workspace root from `payload.get("workspacePaths")` and target file ancestors, while allowing `docs/specs/INDEX.md` promotion to `Approved` when the conversation transcript contains explicit human approval (`Proceed` / `Approved`) in the latest user turn.
- **Acceptance Criteria**:
  - `AC-014-1`: `hooks.json` uses a top-level hook group with `"hooks": [{"type": "command", "command": "/usr/bin/env python3 ./scripts/spec-gate.py", "timeout": 5}]` (no undefined `${PLUGIN_ROOT}` variable), and `resolve_target_workspace()` inspects `payload.get("workspacePaths")`, `AGY_ACTIVE_WORKSPACE`, `payload.get("cwd")`, and `resolved_target.parents` (`.git` or `docs/specs`) to determine the governing workspace root.
  - `AC-014-2`: `has_recent_user_approval(payload: Dict[str, Any]) -> bool` inspects `transcriptPath` in `payload` and permits `INDEX.md` promotion to `Approved` via `replace_file_content`/`write_to_file` when the latest `USER_INPUT` step contains an explicit approval token (`proceed`, `approve`, `approved`, `yes`, `lgtm`, or `the user has approved this document`), while still blocking unapproved autonomous self-promotion.

### `REQ-015`: Sub-500-Line Modularization of `tests/` in `spec-driven-plugin`
- **Statement**: All Python files in `spec-driven-plugin/tests/` MUST be strictly under 450 lines so no test file triggers the 500-line AST gate (`ast-gate.py`).
- **Acceptance Criteria**:
  - `AC-015-1`: `tests/test_spec_gate.py` (647 lines) is split into `tests/test_spec_gate.py` (< 400 lines) and `tests/test_spec_gate_security.py` (< 400 lines).
  - `AC-015-2`: Every `.py` file under `scripts/` and `tests/` in `spec-driven-plugin` is strictly `< 450` lines.

### `REQ-016`: Content-Hashed Semantic Traceability Verification via Opus Agent (`spec_checker.py`)
- **Statement**: `scripts/spec_checker.py` MUST support semantic traceability verification (`validate_semantic_traceability()` and CLI `--semantic`) backed by a content-hashed audit receipt (`traceability_audit.json`) produced by an Opus/high-reasoning agent (either via the `traceability-auditor` Opus subagent or `--semantic` CLI agent invocation), rejecting `flash`-generated receipts, hash mismatches, or unaddressed requirements.
- **Acceptance Criteria**:
  - `AC-016-1`: `compute_spec_package_hash(package_dir: Path, include_verification: bool = False) -> str` computes a deterministic SHA-256 hash over `spec.md`, `decisions.md`, `design.md`, `tasks.md` (and `verification.md` when `include_verification=True`).
  - `AC-016-2`: `validate_semantic_traceability(package_dir: Path, verify_evidence: bool = False, run_agent: bool = False) -> Tuple[bool, str]` verifies `<package_dir>/traceability_audit.json` (or invokes the CLI agent when `run_agent=True`), checking that:
    1. `spec_hash` matches `compute_spec_package_hash(package_dir, False)` (and `evidence_hash` matches `compute_spec_package_hash(package_dir, True)` when `verify_evidence=True`).
    2. `auditor_model` is a non-flash high-reasoning model (`opus`, `pro`, `inherit`, `deep-model`, `primary-model`) and never contains `flash`.
    3. `verdict` is `"PASS"` and `requirements_evaluated` contains a passing semantic entry (`design_aligned`, `tasks_actionable`, `decisions_consistent`, plus `evidence_verified` when `verify_evidence=True`) with non-empty rationale for every declared requirement ID in `spec.md`.
  - `AC-016-3`: When `verify_active_specification(..., verify_evidence=True)` or `--semantic` is called, `spec_checker.py` enforces `validate_semantic_traceability()`.

### `REQ-017`: Opus `traceability-auditor` Subagent & Approval-Gate Enforcement (`spec-gate.py`)
- **Statement**: `spec-driven-plugin` MUST define an Opus-tier `agents/traceability-auditor.md` subagent, and `scripts/spec-gate.py` MUST require a valid semantic traceability receipt (`traceability_audit.json`) before any specification in `docs/specs/INDEX.md` can be promoted to `Approved`, while rejecting any `traceability-auditor` subagent dispatch that uses `flash` or `flash_lite`.
- **Acceptance Criteria**:
  - `AC-017-1`: `is_unauthorized_status_promotion()` in `scripts/spec-gate.py` calls `checker.validate_semantic_traceability(pkg_dir, verify_evidence=False)` whenever a feature in `docs/specs/INDEX.md` is promoted to `EXECUTION_STATUSES` (`Approved`, `In-Progress`, `Active`), denying the promotion if the semantic receipt is missing, stale, audited by `flash`, or failing.
  - `AC-017-2`: `evaluate_spec_gate()` in `scripts/spec-gate.py` allows the `traceability-auditor` subagent to run during Phase 1 planning (`Draft`/`Planning` status), but denies dispatch if `Model` is set to `"flash"` or `"flash_lite"`.

