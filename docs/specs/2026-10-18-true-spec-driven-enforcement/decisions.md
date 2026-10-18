# Architecture Decision Records (ADR): True Spec-Driven Enforcement

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Implemented`

## `ADR-001`: Enforce Semantic Requirement ID Traceability & Exclude Placeholders
- **Context**: Previously, `scripts/spec_checker.py` only checked that `spec.md` contained a single `REQ-xxx` token and that `decisions.md` and `design.md` were non-empty bytes (`st_size > 0`). Agents could create placeholder files with whitespace and bypass the gate without mapping requirements to design components or implementation tasks. Additionally, regex matching on `REQ-[0-9A-Za-z_-]+` erroneously matched literal prose placeholders such as `REQ-xxx`.
- **Decision**: Parse all unique requirement IDs using `r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"`, explicitly filtering out generic placeholder tokens (`REQ-xxx`, `REQ-XXX`). Verify that each declared requirement ID appears in `design.md` and `tasks.md`, and that `decisions.md` contains at least one `ADR-\d+` or declared requirement ID. Require `tasks.md` as part of the core validated package alongside `spec.md`, `decisions.md`, and `design.md`.
- **Consequences**: Prevents placeholder spec packages, eliminates false matches on prose placeholders, and guarantees every normative requirement has both a design mapping and an actionable task item before execution begins.
- **Addresses**: `REQ-001`, `REQ-003`, `REQ-007`

## `ADR-002`: Split Lifecycle Statuses into Planning, Execution, and Terminal Tiers with Strict Normalization
- **Context**: `ACTIVE_STATUSES` previously grouped `draft` and `planning` together with `approved`, `in-progress`, and `active`. A mutating subagent could execute code changes as soon as an unapproved `draft` spec was scaffolded, violating the human approval gate. Furthermore, human entries in markdown tables frequently contain variations in casing and spacing (e.g. `"In Progress"`, `"Approved "`).
- **Decision**: Normalize statuses using `raw.strip().lower().replace(" ", "-").replace("_", "-")`. Partition statuses into `PLANNING_STATUSES = {"draft", "planning", "review"}`, `EXECUTION_STATUSES = {"approved", "in-progress", "active"}`, and `TERMINAL_STATUSES = {"completed", "implemented", "done", "abandoned", "superseded"}`. `verify_active_specification()` accepts `require_approved: bool = True` (defaulting to `True` for code mutations, and configurable via `--allow-planning`).
- **Consequences**: Agents can scaffold and validate draft specifications during Phase 1 (`spec_checker.py --allow-planning`), while `spec-gate.py` blocks code mutations until the spec status in `docs/specs/INDEX.md` is promoted to `Approved`, `In-Progress`, or `Active` via human approval. Repositories without `docs/specs/` remain unaffected.
- **Addresses**: `REQ-002`

## `ADR-003`: Gate Direct File-Mutation Tools With External Brain & Spec Directory Exemptions
- **Context**: `hooks.json` only matched `invoke_subagent`, leaving direct primary-agent calls (`write_to_file`, `replace_file_content`, `multi_replace_file_content`) completely ungated. However, gating file-writing tools naively would create a chicken-and-egg deadlock where an agent cannot create or update `docs/specs/INDEX.md` or write ephemeral plan dashboards to the agent brain directory (`<appDataDir>/brain/<conversation-id>/`). Furthermore, tool names may carry `client:` or `default_api:` prefixes, and relative file paths must be anchored to `workspace_root` rather than process CWD.
- **Decision**:
  1. Register `scripts/spec-gate.py` in `hooks.json` using matcher `^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$`.
  2. Resolve relative target paths against `workspace_root` (`(Path(workspace_root) / raw).resolve()`).
  3. Automatically allow file writes whose resolved target path is in a recognized runtime artifact directory outside `workspace_root` (`.gemini/antigravity/brain`, `.gemini/antigravity/scratch`, or `AGY_RUNTIME_ARTIFACT_DIR`) or inside `<workspace_root>/docs/specs/`.
  4. Fail closed with diagnostic rejection if the target file argument is missing.
- **Consequences**: Eliminates direct-mutation bypasses while preventing Phase 1 planning deadlocks on brain artifacts and specification files.
- **Addresses**: `REQ-004`

## `ADR-004`: Word-Boundary Subagent Keyword Matching & Domain Cleanup
- **Context**: In `scripts/spec-gate.py`, `is_exempt_subagent()` ran before `is_mutating_subagent()`, allowing any subagent with `TypeName="research"` to mutate files if instructed in its prompt. Evaluating `is_mutating_subagent()` first with substring matching caused generic `"code"` to collide with `"codebase researcher"` roles and prompts. Additionally, `TRANSLATION_TYPES`, `runs/` checks, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE` were leftover artifacts from unrelated plugins.
- **Decision**: Evaluate `is_mutating_subagent()` first using regex word-boundary matching (`\b`), remove generic `"code"` from `MUTATION_KEYWORDS`, and fail closed for unknown subagent types. Remove `TRANSLATION_TYPES`, `runs/` checks, dead fallthrough branches, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE`.
- **Consequences**: Closes role-spoofing vulnerabilities without false-positive blocking of read-only research subagents, simplifies `spec-gate.py`, and makes the plugin domain-agnostic.
- **Addresses**: `REQ-005`, `REQ-008`

## `ADR-005`: Multi-Feature Validation Isolation & Threat Model Scoping
- **Context**: `verify_active_specification()` previously iterated through all active specs and failed immediately if any single spec was incomplete. In multi-feature repositories, a newly added `draft` row in `INDEX.md` would block execution of an already `approved` feature. Furthermore, attempting to gate arbitrary shell commands (`run_command`) at the pre-tool hook layer causes severe false positives on tests and builds.
- **Decision**: Evaluate `EXECUTION_STATUSES` packages first and allow execution if all `EXECUTION_STATUSES` packages pass validation and at least one exists (recording incomplete `PLANNING_STATUSES` packages under `warnings`). Add optional `--feature <feature-id>` filtering. Explicitly declare shell command interception as an out-of-scope non-goal, governed instead by thinking-mode Primary Agent behavioral guardrails.
- **Consequences**: Enables concurrent feature planning and execution without cross-feature blocking, and establishes a clear, enforceable threat model.
- **Addresses**: `REQ-006`

## `ADR-006`: Phase 3 Hardening — Terminal Evidence Verification, Declaration Extraction, Symlink Containment & Mechanical Self-Approval Guard
- **Context**: Architectural review of the Phase 2 implementation identified five residual gaps:
  1. Transitioning a feature to `Implemented` in `docs/specs/INDEX.md` caused `spec_checker.py --verify-evidence` and `--feature <id>` to fail with `no_active_spec` because `TERMINAL_STATUSES` were dropped prior to verification.
  2. `validate_spec_package()` included an undocumented `Governing Specification:.*spec\.md` bypass that skipped `design.md` traceability checks, and `extract_requirement_ids()` scraped all prose mentions in `spec.md` rather than declared requirements.
  3. `parse_specs_index()` checked `len(parts) < 6` rather than `len(parts) != 6`, silently truncating rows with unescaped pipes.
  4. `is_allowed_runtime_artifact_path()` exempted all of `/tmp` and `tempfile.gettempdir()`, allowing in-workspace symlinks pointing to `/tmp` to escape workspace gating, and `payload.get("cwd")` took precedence over `AGY_ACTIVE_WORKSPACE`.
  5. Unconditional write allowance on `docs/specs/INDEX.md` allowed agents to self-promote statuses to `Approved` via tool calls.
- **Decision**:
  1. Allow `verify_active_specification()` to validate `completed`, `implemented`, and `done` specs when `feature_id` is explicitly requested or when `verify_evidence=True` is set and no active specs exist, automatically enforcing `verify_evidence=True` on completed/implemented specs.
  2. Remove the `Governing Specification:.*spec\.md` bypass in `validate_spec_package()` and add `extract_declared_requirement_ids()` for `spec.md` heading/bullet/table declarations.
  3. Enforce `len(parts) != 6` in `parse_specs_index()`.
  4. Narrow `is_allowed_runtime_artifact_path()` to `.gemini/antigravity/brain`, `.gemini/antigravity/scratch`, and `AGY_RUNTIME_ARTIFACT_DIR` (removing generic `/tmp`), block in-workspace symlinks that resolve outside `workspace_path`, and prioritize `AGY_ACTIVE_WORKSPACE` over `payload.get("cwd")`.
  5. In `spec-gate.py`, inspect writes to `docs/specs/INDEX.md` and reject mutations that promote a feature to `EXECUTION_STATUSES` unless that feature already has an `EXECUTION_STATUSES` status in the on-disk `INDEX.md` or `SPEC_GATE_ALLOW_APPROVAL=1` is set.
- **Consequences**: Closes the self-approval and symlink-escape loopholes, restores full `AC-001-2`, `AC-001-3`, and `AC-006-2` compliance, and ensures completed specifications remain verifiable with `--verify-evidence` and `--feature`.
- **Addresses**: `REQ-001`, `REQ-003`, `REQ-004`, `REQ-006`, `REQ-007`, `REQ-008`
