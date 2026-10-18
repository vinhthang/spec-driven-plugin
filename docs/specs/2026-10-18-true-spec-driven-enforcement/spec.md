# Specification: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Implemented`
- **Version**: `1.2.0`
- **Date**: `2026-10-18`

## 1. Problem Statement & Context

`spec-driven-plugin` initially operated as a shallow file-presence check rather than a true Spec-Driven Development (SDD) governance engine. Following Phase 2 implementation and architectural review, the specification governs both the core SDD verification engine and Phase 3 hardening across terminal status verification, traceability strictness, path/symlink security, and mechanical approval protection.

## 2. Threat Model, Authority & Non-Goals

### 2.1 Enforcement Scope & Threat Model
- **In-Scope Vectors**: Mechanically gates direct tool-level file mutations (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) and agent execution dispatches (`invoke_subagent`) within workspaces that have adopted `docs/specs/`.
- **Out-of-Scope (Non-Goals)**:
  - Arbitrary shell command interception via `run_command` (e.g. `sed -i`, `git apply`, bash scripts): Shell execution is governed by Primary Agent thinking-mode behavioral guardrails (`RULE[agent-delegation]`) to avoid false-positive blocking of compilation, test execution, and read-only diagnostics.
  - File-to-feature AST ownership mapping: In v1, spec-gate enforces repository-level authorization (at least one valid specification in `EXECUTION_STATUSES` authorizes workspace mutation); fine-grained per-file ownership is an explicit non-goal.
  - Repositories without `docs/specs/`: Completely exempt; the gate remains strictly opt-in per repository.

### 2.2 Human Approval Authority Boundary
- Transitions of specification packages to `Approved`, `In-Progress`, or `Active` in `docs/specs/INDEX.md` are strictly human-governed actions via explicit user consent ("Proceed").
- Autonomous agents operating in planning mode are strictly forbidden from self-promoting specifications to `EXECUTION_STATUSES`, enforced both by rule constraints and mechanically in `scripts/spec-gate.py`.

---

## 3. Normative Requirements

### `REQ-001`: Cross-Document Requirement ID Traceability
- **Statement**: `scripts/spec_checker.py` MUST extract all valid requirement IDs declared in `spec.md` and verify that every declared requirement ID is referenced at least once in both `design.md` and `tasks.md`, and that `decisions.md` contains at least one `ADR-\d+` or `REQ-\d+` citation.
- **Acceptance Criteria**:
  - `AC-001-1`: Requirement ID matching uses `r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"`. Generic placeholders (such as `REQ-xxx`, `REQ-XXX`) are strictly ignored. In `spec.md`, `extract_declared_requirement_ids()` extracts IDs from structured declarations (headings, bullet lead-ins, or table cells, falling back to full-text extraction only if no structured declarations exist) so historical IDs cited in prose background sections do not become false requirement declarations.
  - `AC-001-2`: `validate_spec_package()` fails with a diagnostic message listing the specific unmapped IDs if any ID declared in `spec.md` is missing from `design.md` or `tasks.md`, or if `decisions.md` does not cite at least one `ADR-\d+` or declared requirement ID. No bypass (such as `Governing Specification: spec.md`) may skip `design.md` requirement ID verification.
  - `AC-001-3`: When `--verify-evidence` is passed or when a target specification has a status in `{"completed", "implemented", "done"}`, `validate_spec_package()` additionally requires `verification.md` to exist, contain non-whitespace text, and reference every requirement ID declared in `spec.md`.

### `REQ-002`: Lifecycle Stage & Approval Gate Separation
- **Statement**: In repositories containing a `docs/specs/` directory, `scripts/spec_checker.py` and `scripts/spec-gate.py` MUST distinguish between planning-stage statuses (`draft`, `planning`, `review`), execution-authorized statuses (`approved`, `in-progress`, `active`), and terminal statuses (`completed`, `implemented`, `done`, `abandoned`, `superseded`).
- **Acceptance Criteria**:
  - `AC-002-1`: Status normalization uses `raw.strip().lower().replace(" ", "-").replace("_", "-")` to handle casing, whitespace, and formatting variations (e.g. `"In Progress"` -> `"in-progress"`).
  - `AC-002-2`: `EXECUTION_STATUSES = {"approved", "in-progress", "active"}`, `PLANNING_STATUSES = {"draft", "planning", "review"}`, and `TERMINAL_STATUSES = {"completed", "implemented", "done", "abandoned", "superseded"}` are canonically defined in `scripts/spec_checker.py`.
  - `AC-002-3`: In repositories containing `docs/specs/`, code-mutating operations require at least one valid specification package in `EXECUTION_STATUSES`. Repositories without `docs/specs/` return `status: "no_spec_framework", valid: True` unconditionally.
  - `AC-002-4`: If only `PLANNING_STATUSES` specifications exist in `docs/specs/INDEX.md`, `verify_active_specification(..., require_approved=True)` returns `valid: False` with `status: "unapproved_spec"` and instructs the agent to obtain human approval before mutating code.

### `REQ-003`: Package Validation Alignment, Non-Whitespace Enforcement & Path Containment
- **Statement**: `validate_spec_package()` in `scripts/spec_checker.py` MUST require `spec.md`, `decisions.md`, `design.md`, and `tasks.md` to contain non-whitespace text and MUST enforce strict 6-column table parsing and workspace path containment.
- **Acceptance Criteria**:
  - `AC-003-1`: Required core package files are `["spec.md", "decisions.md", "design.md", "tasks.md"]`.
  - `AC-003-2`: Files containing only whitespace (`content.strip() == ""`) are rejected as empty (`status: "incomplete_package"`).
  - `AC-003-3`: All resolved package candidate paths (including `specs_dir / feat_id` and explicit `spec_path`) are verified via `Path.is_relative_to(root)`. Any path resolving outside `workspace_root` (including directory traversal via `..` in `feature_id`) is rejected with `status: "invalid_path"`.
  - `AC-003-4`: `parse_specs_index()` splits Markdown table cells using an unescaped-pipe regex (`re.split(r"(?<!\\)\|", ...)`) and raises `ValueError` if `len(parts) != 6` (rejecting both `< 6` and `> 6` column rows as `status: "corrupt_index"`).

### `REQ-004`: Direct Mutation Tool Gate, Symlink Containment & Mechanical Approval Protection
- **Statement**: `hooks.json` and `scripts/spec-gate.py` MUST gate direct file-mutation tools (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) and `invoke_subagent`, supporting prefixed tool names, while restricting external writes to recognized runtime artifact directories, preventing symlink escapes, and blocking unauthorized self-approval in `docs/specs/INDEX.md`.
- **Acceptance Criteria**:
  - `AC-004-1`: `hooks.json` registers `scripts/spec-gate.py` using regex matcher `^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$`.
  - `AC-004-2`: Target file path resolution in `evaluate_spec_gate()`:
    1. Workspace root is resolved with precedence `os.environ.get("AGY_ACTIVE_WORKSPACE") or payload.get("cwd") or os.getcwd()`.
    2. The raw target path is extracted from `args.get("TargetFile") or args.get("target_file") or args.get("file_path") or args.get("path")`. If missing, the gate fails closed (`decision: "deny"`).
    3. Both the lexical path `lexical_target = workspace_path / raw_path` (when relative) and `resolved_target = lexical_target.resolve()` are evaluated. If `lexical_target` is inside `workspace_path` but `resolved_target` escapes `workspace_path` (via symlink), the gate fails closed (`decision: "deny"`).
    4. If `resolved_target` is outside `workspace_path`, it is allowed ONLY if `is_allowed_runtime_artifact_path(resolved_target)` is `True` (matching `.gemini/antigravity/brain`, `.gemini/antigravity/scratch`, or `os.environ.get("AGY_RUNTIME_ARTIFACT_DIR")`; generic `/tmp` is NOT unconditionally exempt).
    5. If `resolved_target` is inside `workspace_path / "docs" / "specs"`, authoring is allowed subject to the self-approval guard in `AC-004-4`.
  - `AC-004-3`: When a direct file-mutation tool targets a file within `workspace_root` outside `docs/specs/` in a repository with `docs/specs/`, `evaluate_spec_gate()` requires a valid specification package in `EXECUTION_STATUSES`.
  - `AC-004-4`: When a direct file-mutation tool targets `docs/specs/INDEX.md`, `evaluate_spec_gate()` inspects the incoming content (`Content`, `ReplacementContent`, `ReplacementChunks`). If the edit introduces a new feature row or promotes an existing feature row into `EXECUTION_STATUSES` (`approved`, `in-progress`, `active`) that was not already in `EXECUTION_STATUSES` on disk, and `os.environ.get("SPEC_GATE_ALLOW_APPROVAL") != "1"`, the gate returns `decision: "deny"` with a reason explaining that status promotion to `Approved`/`In-Progress`/`Active` requires human approval.

### `REQ-005`: Fail-Closed Subagent Evaluation & Domain Leakage Cleanup
- **Statement**: `scripts/spec-gate.py` MUST evaluate mutation indicators before role exemptions using regex word boundaries, remove dead code in `evaluate_spec_gate()`, and remove translation-specific and foreign plugin artifacts.
- **Acceptance Criteria**:
  - `AC-005-1`: `is_mutating_subagent(sa)` is checked before `is_exempt_subagent(sa)`. Mutation keywords (`implement`, `modify`, `compiler`, `executor`, `builder`, `patch`, `write_to_file`, `replace_file_content`) MUST be matched using regex word boundaries (`\b`) to prevent false-positive collisions with read-only roles (e.g. matching `'code'` in `'codebase researcher'`), and generic `'code'` is removed from `MUTATION_KEYWORDS`.
  - `AC-005-2`: Only explicitly read-only research subagents without mutation keywords are exempt; unknown subagent types fail closed (`requires_gate = True`).
  - `AC-005-3`: `TRANSLATION_TYPES`, `"runs/"` prompt checks, `EXEMPT_TYPES`, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE` are removed from `scripts/spec-gate.py`.

### `REQ-006`: Feature-Scoped Validation & Terminal-Status Evidence Verification
- **Statement**: `verify_active_specification()` in `scripts/spec_checker.py` MUST NOT allow an incomplete `draft` or `planning` specification to block execution when at least one complete, valid `EXECUTION_STATUSES` specification package exists in `docs/specs/INDEX.md`, and MUST support `--feature <feature-id>` and `--verify-evidence` across both active and terminal (`completed`, `implemented`, `done`) specifications.
- **Acceptance Criteria**:
  - `AC-006-1`: When multiple specs exist in `INDEX.md`, `verify_active_specification()` evaluates `EXECUTION_STATUSES` specs independently from `PLANNING_STATUSES` specs; if all `EXECUTION_STATUSES` specs are valid and complete (and at least one exists), verification succeeds while reporting any incomplete `PLANNING_STATUSES` specs in `warnings`.
  - `AC-006-2`: Passing `--feature <feature-id>` (or `feature_id` to `verify_active_specification()`) validates that specific feature package directly, including when its status is in `TERMINAL_STATUSES` (`completed`, `implemented`, `done`), automatically enforcing `verify_evidence=True` for terminal completed/implemented specs.
  - `AC-006-3`: When `verify_evidence=True` (`--verify-evidence`) is called without `--feature` and no `EXECUTION_STATUSES` or `PLANNING_STATUSES` specs exist in `INDEX.md`, `verify_active_specification()` validates `completed` / `implemented` / `done` specification packages in `INDEX.md` so post-implementation evidence audits succeed.

### `REQ-007`: Self-Contained Rule & Skill Contract Alignment
- **Statement**: `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` MUST align on required documents (`spec.md`, `decisions.md`, `design.md`, `tasks.md` for planning; `verification.md` for verification), fast-path interaction with mechanical gating, and self-contained fallback workflows.
- **Acceptance Criteria**:
  - `AC-007-1`: `skills/spec-standard/SKILL.md` updates its *Scaling Switches* section so `spec.md`, `decisions.md`, `design.md`, and `tasks.md` form the mandatory core package enforced by `spec_checker.py`, with `verification.md` populated during Phase 2 verification.
  - `AC-007-2`: Both `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` document standalone fallbacks when `/grill-me`, `/plan`, or optional external plugins are not installed, and clarify that in repositories containing `docs/specs/`, `spec-gate.py` mechanically requires an active execution-authorized spec for all workspace file edits outside `docs/specs/`.

### `REQ-008`: Self-Contained Unit & Integration Test Suite & Package Hygiene
- **Statement**: All unit and CLI tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py` MUST be 100% self-contained using temporary directories without referencing external repositories, and the in-repo specification package must pass `spec_checker.py --workspace . --verify-evidence`.
- **Acceptance Criteria**:
  - `AC-008-1`: Zero references to `ai-review-plugin` or `TRANSLATION_TYPES` remain anywhere in `tests/` or `scripts/`, and stray non-standard files (such as `reviews/spec-v1.json`) are removed from `docs/specs/2026-10-18-true-spec-driven-enforcement/`.
  - `AC-008-2`: Unit tests cover `REQ-001` through `REQ-007`, including terminal-status `--verify-evidence` / `--feature` validation, removal of the `Governing Specification` bypass, `!= 6` column rejection, symlink escape rejection, self-approval rejection on `docs/specs/INDEX.md`, and structured requirement declaration extraction.
  - `AC-008-3`: Running `pytest -v` and `python3 scripts/spec_checker.py --workspace . --verify-evidence --json` from the repository root both pass with exit code `0`, and their verbatim outputs are recorded in `verification.md`.
