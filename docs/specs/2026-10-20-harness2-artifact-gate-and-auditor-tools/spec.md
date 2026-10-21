# Specification: Harness² Referenced Artifact Verification Gate & Traceability Auditor Tool Permissions

## 1. Overview & Context
In [`google-research/harness2`](https://github.com/google-research/harness2), `harness2/core/tree.py::validate` verifies that every relative file path referenced in documentation exists in the workspace and that every Python script compiles cleanly. Additionally, `agents/traceability-auditor.md` in `spec-driven-plugin` declared only `tools: [write_to_file]`, omitting `read_file`, `view_file`, and `write_file`. Finally, `spec_checker.py` required support for domain-prefixed requirement IDs (`REQ-AE-001`, `REQ-DSL-001`) and `spec-gate.py` required explicit allowance for global Antigravity configuration files under `~/.gemini/config/`.

---

## 2. Normative Requirements (EARS Syntax)

### `REQ-023` — Traceability Auditor Read/Write Tool Permissions
- **WHEN** `traceability-auditor` is invoked to audit a specification package in `docs/specs/<feature-id>/`, **THE** `agents/traceability-auditor.md` frontmatter **SHALL** declare `tools: [read_file, view_file, write_file, write_to_file]` so the subagent can directly read `spec.md`, `decisions.md`, `design.md`, `tasks.md`, and `verification.md` and write `traceability_audit.json`.
- **Acceptance Criteria**:
  - `agents/traceability-auditor.md` line 5 specifies `tools: [read_file, view_file, write_file, write_to_file]`.

### `REQ-024` — Referenced Artifact Existence & Compilation Gate in `verification.md`
- **WHEN** `scripts/spec_checker.py` validates a specification package with `--verify-evidence` (`verify_evidence=True`), **THE** checker **SHALL** extract all relative Python script/test paths matching `(?:scripts|tests)/[A-Za-z0-9_.\-/]+\.py` cited in `verification.md` and verify that each referenced file exists in the repository root and compiles without `SyntaxError` via `compile(src, rel_path, "exec")`.
- **Acceptance Criteria**:
  - `check_referenced_artifacts(spec_dir: Path, repo_root: Optional[Path] = None) -> List[str]` is implemented in `scripts/spec_checker.py`.
  - If `verification.md` cites a relative `scripts/*.py` or `tests/*.py` path that does not exist on disk under `repo_root`, `validate_spec_package(..., verify_evidence=True)` fails with an actionable error naming the missing artifact.
  - If a cited `scripts/*.py` or `tests/*.py` file contains invalid Python syntax, `validate_spec_package(..., verify_evidence=True)` fails with a compilation error.

### `REQ-025` — Domain-Prefixed Requirement ID Pattern Support
- **WHEN** `scripts/spec_checker.py` extracts requirement IDs from `spec.md`, `decisions.md`, `design.md`, `tasks.md`, or `verification.md`, **THE** checker **SHALL** match both standard numeric IDs (`REQ-001`) and domain-prefixed IDs (`REQ-AE-001`, `REQ-DSL-001`, `REQ-TOC-1`, `REQ-MOD-EVAL-1`, `REQ-2STG-1`) via `REQ_ID_PATTERN = re.compile(r"\b(?:REQ|FLOW|ALIGN)-(?:[A-Z0-9]+-)*\d+\b")`.
- **Acceptance Criteria**:
  - Historical specifications in `attention-guard` and `agent-translator` using domain-prefixed `REQ-*` IDs pass `validate_spec_package()`.

### `REQ-026` — Global `~/.gemini/config/` Allowance in `spec-gate.py`
- **WHEN** `scripts/spec-gate.py` evaluates a file mutation targeting global Antigravity configuration files (`~/.gemini/config/rules/`, `~/.gemini/config/scripts/`, `~/.gemini/config/skills/`, `~/.gemini/config/hooks.json`) that do not resolve via symlinks to a `docs/specs/` repository, **THE** gate **SHALL** allow the operation in accordance with `RULE[workspace-boundary]`.
- **Acceptance Criteria**:
  - `is_allowed_runtime_artifact_path(target_path)` returns `True` for paths under `.gemini/config/{rules,scripts,skills}` and `.gemini/config/hooks.json`.


### `REQ-027` — `/goal` Autonomous Approval & Antigravity 2.0 Tool Schema Parity in `spec-gate.py`
- **WHEN** the user invokes `/goal` in the conversation transcript, **THE** `has_recent_user_approval()` function in `scripts/spec-gate.py` **SHALL** recognize `/goal` as explicit human authorization per `RULE[explicit-approval]`, and **THE** gate **SHALL** intercept Antigravity 2.0 `write_file` / `edit_file` (`Path`) and flat `invoke_subagent` calls alongside legacy `write_to_file` / `replace_file_content` (`TargetFile`) and `Subagents=[...]`.
- **Acceptance Criteria**:
  - `has_recent_user_approval()` returns `True` when `/goal` is present in the latest user turn (or any user turn initiating the active `/goal` session without `/plan`).
  - `FILE_MUTATION_TOOLS` includes `write_file`, `edit_file`, `default_api:write_file`, `default_api:edit_file`, `client:write_file`, `client:edit_file`, and resolves `args.get("Path")`.

### `REQ-028` — Target Repository Resolution from Absolute Paths in `invoke_subagent` Prompts
- **WHEN** `scripts/spec-gate.py` evaluates an `invoke_subagent` tool call whose `Prompt` references absolute filesystem paths (`/[A-Za-z0-9_.\-/]+`) belonging to a repository containing `docs/specs/INDEX.md` (such as `~/.gemini/config/plugins/<plugin>`), **THE** gate **SHALL** resolve those target repositories via `resolve_target_workspace()` and validate their `docs/specs/INDEX.md` rather than falling back to unrelated `workspacePaths` repositories.
- **Acceptance Criteria**:
  - `extract_prompt_workspaces(all_prompts: str, candidate_workspaces: List[Path]) -> List[Path]` resolves both `candidate_workspaces` and absolute paths mentioned in `all_prompts` that resolve to a parent directory containing `docs/specs/INDEX.md`.
  - Dispatching a subagent targeting a plugin with a valid spec succeeds even when `workspacePaths` contains an unrelated repo with an incomplete draft spec.
