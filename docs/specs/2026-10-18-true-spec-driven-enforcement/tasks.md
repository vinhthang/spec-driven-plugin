# Execution Tasks: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Approved`

## Phase 2 Implementation Checklist (For Delegated Agent)

- [x] **Task 1: Implement status normalization, canonical tiers, and path containment in `scripts/spec_checker.py`** (`REQ-002`, `REQ-003`, `REQ-006`)
  - Define canonical status sets: `PLANNING_STATUSES = {"draft", "planning", "review"}`, `EXECUTION_STATUSES = {"approved", "in-progress", "active"}`, and `TERMINAL_STATUSES = {"completed", "implemented", "done", "abandoned", "superseded"}`.
  - Implement `normalize_status(raw: str) -> str` (`raw.strip().lower().replace(" ", "-").replace("_", "-")`).
  - Update `parse_specs_index()` to split on unescaped pipes (`re.split(r"(?<!\\)\|", ...)`) and unescape `\|`.
  - Add path traversal protection: reject `feature_id` containing `..`, `/`, or `\\`, and enforce `cand.resolve().is_relative_to(root)` on all resolved candidate directories.
- [x] **Task 2: Implement `REQ-\d+` traceability and 4-document validation in `scripts/spec_checker.py`** (`REQ-001`, `REQ-003`, `REQ-006`)
  - Implement `extract_requirement_ids(text: str) -> List[str]` using `r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"` while filtering placeholder tokens (`REQ-xxx`, `REQ-XXX`).
  - Update `validate_spec_package(package_dir, verify_evidence=False)` to require non-whitespace `spec.md`, `decisions.md`, `design.md`, and `tasks.md` (plus `verification.md` when `verify_evidence=True`).
  - Verify that every declared requirement ID in `spec.md` appears in `design.md` and `tasks.md` (and `verification.md` when `verify_evidence=True`), and that `decisions.md` contains at least one `ADR-\d+` or declared requirement ID.
  - Update `verify_active_specification()` and CLI `main()` with arguments (`--feature`, `--allow-planning`, `--verify-evidence`, `--workspace`, `--json`, `--quiet`) and standardized exit codes (0/1/2).
- [x] **Task 3: Harden `scripts/spec-gate.py` and expand `hooks.json`** (`REQ-002`, `REQ-004`, `REQ-005`)
  - Update `hooks.json` matcher to `"^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$"`.
  - Remove `TRANSLATION_TYPES`, `EXEMPT_TYPES`, `"runs/"` prompt exemptions, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE` from `scripts/spec-gate.py`.
  - Check `is_mutating_subagent(sa)` before `is_exempt_subagent(sa)` using regex word boundaries (`\b`) with refined `MUTATION_KEYWORDS` (removing generic `'code'`).
  - Handle direct file-mutation tools: fail closed if target path argument is missing, resolve relative paths against `workspace_root`, exempt external paths (outside workspace root) and `docs/specs/` paths, and require `verify_active_specification(workspace_root, require_approved=True)` for all other workspace file mutations.
- [x] **Task 4: Align `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` contracts** (`REQ-007`)
  - Reconcile *Scaling Switches* in `skills/spec-standard/SKILL.md` with the 4-document planning baseline (`spec.md`, `decisions.md`, `design.md`, `tasks.md`) + `verification.md` for Phase 2 verification.
  - Document human approval authority boundaries and standalone fallbacks when slash commands are absent.
- [x] **Task 5: Rewrite & expand unit tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py`** (`REQ-008`)
  - Remove all references to `../ai-review-plugin` and legacy translation symbols in `tests/test_spec_gate.py`.
  - Add self-contained unit tests covering `AC-001-1` through `AC-008-3`.
- [x] **Task 6: Run verification suite and record verbatim output in `verification.md`** (`REQ-001`, `REQ-008`)
  - Run `pytest -v` and `python3 scripts/spec_checker.py --workspace . --verify-evidence --json`.
  - Append verbatim outputs mapped to `REQ-001` through `REQ-008` in `docs/specs/2026-10-18-true-spec-driven-enforcement/verification.md`.
