# Specification: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Implemented`
- **Version**: `1.1.0`
- **Date**: `2026-10-18`

## 1. Problem Statement & Context

`spec-driven-plugin` currently operates as a shallow file-presence check rather than a true Spec-Driven Development (SDD) governance engine. Specifically:
1. `scripts/spec_checker.py` only checks that `spec.md`, `decisions.md`, and `design.md` have `st_size > 0` and that `spec.md` matches a single requirement regex, without verifying cross-document requirement traceability or `tasks.md` coverage.
2. `ACTIVE_STATUSES` treats unapproved `draft` and `planning` specifications identically to `approved` and `in-progress` specifications, permitting code mutations before human approval.
3. `hooks.json` and `scripts/spec-gate.py` only intercept `invoke_subagent`, allowing primary agents to mutate code directly via `write_to_file` and `replace_file_content`, and evaluate role exemptions (`is_exempt_subagent`) before mutation checks (`is_mutating_subagent`), enabling trivial role-spoofing bypasses.
4. `scripts/spec-gate.py` and `tests/test_spec_gate.py` contain leaked translation-pipeline exemptions (`TRANSLATION_TYPES`, `runs/`), dead mutation-detection branches, and a hardcoded path dependency on `../ai-review-plugin`.

## 2. Threat Model, Authority & Non-Goals

### 2.1 Enforcement Scope & Threat Model
- **In-Scope Vectors**: Mechanically gates direct tool-level file mutations (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) and agent execution dispatches (`invoke_subagent`) within workspaces that have adopted `docs/specs/`.
- **Out-of-Scope (Non-Goals)**:
  - Arbitrary shell command interception via `run_command` (e.g. `sed -i`, `git apply`, bash scripts): Shell execution is governed by Primary Agent thinking-mode behavioral guardrails (`RULE[agent-delegation]`) to avoid false-positive blocking of compilation, test execution, and read-only diagnostics.
  - File-to-feature AST ownership mapping: In v1, spec-gate enforces repository-level authorization (at least one valid specification in `EXECUTION_STATUSES` authorizes workspace mutation); fine-grained per-file ownership is an explicit non-goal.
  - Repositories without `docs/specs/`: Completely exempt; the gate remains strictly opt-in per repository.

### 2.2 Human Approval Authority Boundary
- Transitions of specification packages to `Approved`, `In-Progress`, or `Active` in `docs/specs/INDEX.md` are strictly human-governed actions via explicit user consent ("Proceed").
- Autonomous agents operating in planning mode are strictly forbidden from self-promoting specifications to `EXECUTION_STATUSES`.

---

## 3. Normative Requirements

### `REQ-001`: Cross-Document Requirement ID Traceability
- **Statement**: `scripts/spec_checker.py` MUST extract all valid requirement IDs declared in `spec.md` and verify that every declared requirement ID is referenced at least once in both `design.md` and `tasks.md`, and that `decisions.md` contains at least one `ADR-\d+` or `REQ-\d+` citation.
- **Acceptance Criteria**:
  - `AC-001-1`: Requirement ID matching uses `r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"`. Generic placeholders (such as `REQ-xxx`, `REQ-XXX`) are strictly ignored and never registered as active requirement IDs.
  - `AC-001-2`: `validate_spec_package()` fails with a diagnostic message listing the specific unmapped IDs if any ID from `spec.md` is missing from `design.md` or `tasks.md`, or if `decisions.md` does not cite at least one `ADR-\d+` or declared requirement ID.
  - `AC-001-3`: When `--verify-evidence` (or status `completed` / `implemented`) is evaluated, `validate_spec_package()` additionally requires `verification.md` to exist, be non-empty, and reference every requirement ID from `spec.md`.

### `REQ-002`: Lifecycle Stage & Approval Gate Separation
- **Statement**: In repositories containing a `docs/specs/` directory, `scripts/spec_checker.py` and `scripts/spec-gate.py` MUST distinguish between planning-stage statuses (`draft`, `planning`, `review`) and execution-authorized statuses (`approved`, `in-progress`, `active`).
- **Acceptance Criteria**:
  - `AC-002-1`: Status normalization uses `raw.strip().lower().replace(" ", "-").replace("_", "-")` to handle casing, whitespace, and formatting variations (e.g. `"In Progress"` -> `"in-progress"`).
  - `AC-002-2`: `EXECUTION_STATUSES = {"approved", "in-progress", "active"}`, `PLANNING_STATUSES = {"draft", "planning", "review"}`, and `TERMINAL_STATUSES = {"completed", "implemented", "done", "abandoned", "superseded"}` are canonically defined in `scripts/spec_checker.py`.
  - `AC-002-3`: In repositories containing `docs/specs/`, code-mutating operations require at least one valid specification package in `EXECUTION_STATUSES`. Repositories without `docs/specs/` return `status: "no_spec_framework", valid: True` unconditionally.
  - `AC-002-4`: If only `PLANNING_STATUSES` specifications exist in `docs/specs/INDEX.md`, `verify_active_specification(..., require_approved=True)` returns `valid: False` with `status: "unapproved_spec"` and instructs the agent to obtain human approval before mutating code.

### `REQ-003`: Package Validation Alignment, Non-Whitespace Enforcement & Path Containment
- **Statement**: `validate_spec_package()` in `scripts/spec_checker.py` MUST require `spec.md`, `decisions.md`, `design.md`, and `tasks.md` to contain non-whitespace text and MUST enforce that all resolved candidate paths stay within the workspace root.
- **Acceptance Criteria**:
  - `AC-003-1`: Required core package files are `["spec.md", "decisions.md", "design.md", "tasks.md"]`.
  - `AC-003-2`: Files containing only whitespace (`content.strip() == ""`) are rejected as empty (`status: "incomplete_package"`).
  - `AC-003-3`: All resolved package candidate paths (including `specs_dir / feat_id` and explicit `spec_path`) are verified via `Path.is_relative_to(root)`. Any path resolving outside `workspace_root` (including directory traversal via `..` in `feature_id`) is rejected with `status: "invalid_path"`.
  - `AC-003-4`: `parse_specs_index()` splits Markdown table cells using an unescaped-pipe regex (`re.split(r"(?<!\\)\|", ...)`) so escaped pipes (`\|`) inside table cells do not corrupt column parsing.

### `REQ-004`: Direct Mutation Tool Gate & Authoring Exemptions
- **Statement**: `hooks.json` and `scripts/spec-gate.py` MUST gate direct file-mutation tools (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) and `invoke_subagent`, supporting prefixed tool names, while exempting runtime artifacts outside the workspace and specification files inside `docs/specs/`.
- **Acceptance Criteria**:
  - `AC-004-1`: `hooks.json` registers `scripts/spec-gate.py` using regex matcher `^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$`.
  - `AC-004-2`: Target file path resolution in `evaluate_spec_gate()`:
    1. The raw target path is extracted from `args.get("TargetFile") or args.get("target_file") or args.get("file_path") or args.get("path")`. If missing, the gate fails closed (`decision: "deny"`) with a clear diagnostic reason.
    2. Relative paths are resolved strictly against `workspace_root` (`(Path(workspace_root) / raw_path).resolve()`).
    3. If the resolved path is outside `workspace_root` (such as agent runtime brain artifacts in `<appDataDir>/brain/`), the operation is allowed unconditionally.
    4. If the resolved path is within `workspace_root` and inside `docs/specs/`, the operation is allowed unconditionally to permit Phase 1 specification authoring.
  - `AC-004-3`: When a direct file-mutation tool targets a file within `workspace_root` outside `docs/specs/` in a repository with `docs/specs/`, `evaluate_spec_gate()` requires a valid specification package in `EXECUTION_STATUSES`.

### `REQ-005`: Fail-Closed Subagent Evaluation & Domain Leakage Cleanup
- **Statement**: `scripts/spec-gate.py` MUST evaluate mutation indicators before role exemptions using regex word boundaries, remove dead code in `evaluate_spec_gate()`, and remove translation-specific and foreign plugin artifacts.
- **Acceptance Criteria**:
  - `AC-005-1`: `is_mutating_subagent(sa)` is checked before `is_exempt_subagent(sa)`. Mutation keywords (`implement`, `modify`, `compiler`, `executor`, `builder`, `patch`, `write_to_file`, `replace_file_content`) MUST be matched using regex word boundaries (`\b`) to prevent false-positive collisions with read-only roles (e.g. matching `'code'` in `'codebase researcher'`), and generic `'code'` is removed from `MUTATION_KEYWORDS`.
  - `AC-005-2`: Only explicitly read-only research subagents without mutation keywords are exempt; unknown subagent types fail closed (`requires_gate = True`).
  - `AC-005-3`: `TRANSLATION_TYPES`, `"runs/"` prompt checks, `EXEMPT_TYPES`, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE` are removed from `scripts/spec-gate.py`.

### `REQ-006`: Feature-Scoped Validation Without Cross-Stream Blocking
- **Statement**: `verify_active_specification()` in `scripts/spec_checker.py` MUST NOT allow an incomplete `draft` or `planning` specification to block execution when at least one complete, valid `EXECUTION_STATUSES` specification package exists in `docs/specs/INDEX.md`, and MUST support optional `--feature <feature-id>` targeting.
- **Acceptance Criteria**:
  - `AC-006-1`: When multiple specs exist in `INDEX.md`, `verify_active_specification()` evaluates `EXECUTION_STATUSES` specs independently from `PLANNING_STATUSES` specs; if at least one `EXECUTION_STATUSES` spec is valid and complete, verification succeeds (while reporting incomplete draft specs in a `warnings` list).
  - `AC-006-2`: Passing `--feature <feature-id>` to `spec_checker.py` (or `feature_id` to `verify_active_specification()`) validates that specific feature package directly.

### `REQ-007`: Self-Contained Rule & Skill Contract Alignment
- **Statement**: `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` MUST align on required documents (`spec.md`, `decisions.md`, `design.md`, `tasks.md` for planning; `verification.md` for verification) and define self-contained fallback workflows when slash commands are unavailable.
- **Acceptance Criteria**:
  - `AC-007-1`: `skills/spec-standard/SKILL.md` updates its *Scaling Switches* section so `spec.md`, `decisions.md`, `design.md`, and `tasks.md` form the mandatory core package enforced by `spec_checker.py`, with `verification.md` populated during Phase 2 verification.
  - `AC-007-2`: Both `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` document standalone fallbacks when `/grill-me`, `/plan`, or optional external plugins are not installed.

### `REQ-008`: Self-Contained Unit & Integration Test Suite
- **Statement**: All unit and CLI tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py` MUST be 100% self-contained using temporary directories without referencing external repositories.
- **Acceptance Criteria**:
  - `AC-008-1`: Zero references to `ai-review-plugin` or `TRANSLATION_TYPES` remain anywhere in `tests/` or `scripts/`.
  - `AC-008-2`: Unit tests cover `REQ-001` through `REQ-007` (traceability failures, unapproved status rejection, role-spoofing rejection, direct file-mutation tool gating, authoring allowances, escaped-pipe parsing, path traversal rejection, status normalization, and multi-feature isolation).
  - `AC-008-3`: Running `pytest -v` from the repository root passes with 0 failures and 0 external filesystem dependencies.
