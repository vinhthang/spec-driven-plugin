# Architecture Decision Records (ADR): Codebase Simplification & Parser Unification

- **Feature ID**: `2026-10-19-simplification-and-deduplication`
- **Status**: `Planning`

## `ADR-007`: Extract `parse_specs_index_text()` and `resolve_package_dir()` in `spec_checker.py`
- **Context**: `scripts/spec_checker.py` reached 489 lines (11 lines below the 500-line AST gate threshold), and `scripts/spec-gate.py` duplicated Markdown table parsing logic to inspect in-memory projected `INDEX.md` content.
- **Decision**: Extract `parse_specs_index_text(content: str) -> List[Dict[str, str]]` as the single Markdown table parser in `spec_checker.py`, and extract candidate path resolution into `resolve_package_dir()`. Reuse `parse_specs_index_text()` inside `spec-gate.py`.
- **Consequences**: Eliminates duplicate table-parsing code in `spec-gate.py`, keeps `spec_checker.py` well under 450 lines, and makes `verify_active_specification()` concise and easy to read.
- **Addresses**: `REQ-009`, `REQ-010`

## `ADR-008`: Fail-Closed Partial-Cell Replacement & Contiguous Path-Part Matching in `spec-gate.py`
- **Context**: In `is_unauthorized_status_promotion()`, if `TargetContent` was not found in `disk_text` or if `ReplacementContent` was a 1-column snippet (`"| Approved |"`), the 3-column scanner could be bypassed. Additionally, `is_allowed_runtime_artifact_path()` used raw substring matching (`in target_str`).
- **Decision**:
  1. Fail closed in `is_unauthorized_status_promotion()` when `TargetContent` is empty or not found in `disk_text`, when `parse_specs_index_text(projected_text)` fails, or when a partial replacement introduces an `EXECUTION_STATUSES` token.
  2. Match contiguous path parts `(".gemini", "antigravity", "brain")` or `(".gemini", "antigravity", "scratch")` in `target_path.parts` rather than raw string substrings.
- **Consequences**: Closes partial-cell replacement and substring-spoofing bypasses while remaining simple and self-contained.
- **Addresses**: `REQ-010`, `REQ-011`, `REQ-012`

## `ADR-009`: Single-Signature `resolve_package_dir()` & Sub-450-Line Test Suite Split
- **Context**: `resolve_package_dir()` used a confusing `isinstance(spec, dict)` positional parameter shift, and `tests/test_spec_gate.py` grew to 647 lines (exceeding the 500-line `ast-gate.py` limit).
- **Decision**: Standardize `resolve_package_dir(spec: Dict[str, str], root: Path, specs_dir: Optional[Path] = None)` on a single dictionary-based signature and split `tests/test_spec_gate.py` into `tests/test_spec_gate.py` and `tests/test_spec_gate_security.py` (all files `< 450` lines).
- **Consequences**: Eliminates parameter-shifting complexity and keeps every script and test file in `spec-driven-plugin` under the 500-line AST threshold.
- **Addresses**: `REQ-013`, `REQ-015`

## `ADR-010`: Valid `hooks.json` Schema, `workspacePaths` Resolution & Transcript-Backed Approval in `spec-gate.py`
- **Context**:
  1. `spec-driven-plugin/hooks.json` lacked the required inner `"hooks": [{"type": "command", "command": "..."}]` array and referenced an undefined `${PLUGIN_ROOT}` variable, whereas Antigravity sets `os.getcwd()` to the directory containing `hooks.json` and passes active workspaces in `payload["workspacePaths"]` (not `"cwd"`). Because `spec-gate.py` fell back to `os.getcwd()`, any file outside `~/.gemini/config` was treated as outside the workspace!
  2. `is_unauthorized_status_promotion()` blocked `replace_file_content` on `INDEX.md` even after the user explicitly replied `"proceed"` in chat because the IDE does not inject `SPEC_GATE_ALLOW_APPROVAL=1` into `PreToolUse` hooks.
- **Decision**:
  1. Fix `hooks.json` to use `"spec-gate-plugin": {"PreToolUse": [{"matcher": "...", "hooks": [{"type": "command", "command": "/usr/bin/env python3 ./scripts/spec-gate.py", "timeout": 5}]}]}`.
  2. Extract `workspacePaths` from `payload` and walk `resolved_target.parents` in `resolve_target_workspace()` to locate the enclosing repository root (`.git` or `docs/specs`) for file mutations, and check all `workspacePaths` for subagent dispatches.
  3. Check `has_recent_user_approval(payload)` via `transcriptPath` so that if the latest `USER_INPUT` step contains explicit user approval (`proceed`, `approve`, `approved`, `yes`, `lgtm`, or `the user has approved this document`), promoting `Planning`/`Draft` -> `Approved` in `INDEX.md` is permitted via standard file-editing tools.
- **Consequences**: `spec-driven-plugin/hooks.json` works standalone, multi-workspace sessions and normal workspace edits resolve their true repository root rather than `os.getcwd()`, and human `"Proceed"` approval in chat directly unlocks `INDEX.md` promotion to `Approved`.
- **Addresses**: `REQ-014`

## `ADR-011`: Hybrid Content-Hashed Semantic Traceability via Opus Subagent & CLI (`traceability_audit.json`)
- **Context**: Pure regex matching (`REQ-\d+`) in `validate_spec_package()` only verifies that requirement ID tokens appear as strings in `design.md`, `tasks.md`, and `verification.md`. An agent can game regex checks by pasting requirement IDs in a header without writing real architectural design, actionable tasks, or falsifiable test evidence. However, calling an LLM synchronously inside `spec-gate.py` on every `write_to_file` hook would exceed the 5-second `PreToolUse` hook timeout.
- **Decision**:
  1. Require a SHA-256 content-hashed semantic audit receipt (`<package_dir>/traceability_audit.json`) generated by an **Opus/high-reasoning** agent (`agents/traceability-auditor.md` invoked with `Model="pro"`/`"inherit"`, or `spec_checker.py --semantic` invoking the headless CLI agent).
  2. Enforce `validate_semantic_traceability()` at two high-leverage boundaries: (a) in `spec-gate.py` when promoting a spec to `Approved` in `docs/specs/INDEX.md`, and (b) in `spec_checker.py` when `--verify-evidence` or `--semantic` is passed. Keep intermediate file-mutation hook checks fast (<10ms).
  3. Mechanically reject `flash` / `flash_lite` models for `traceability-auditor` dispatches and in `traceability_audit.json` (`auditor_model`). (Amended by `ADR-012`, 2026-10-19: superseded by the tier-aware auditor policy.)
- **Consequences**: Prevents superficial regex-only specifications while preserving sub-10ms `PreToolUse` hook latency during normal coding.
- **Addresses**: `REQ-016`, `REQ-017`

## `ADR-012`: Tier-Aware Auditor Policy — Gemini 3.8 Flash High Approved (amends `ADR-011` item 3)
- **Context**: The operator no longer has Claude models in Antigravity (Google is removing them), so an Opus-only auditor rule would leave no approved high-reasoning auditor for `traceability-auditor` dispatches, `--semantic` CLI audits, or the MCP reviewer server. The blanket `flash` ban in `ADR-011` item 3 was aimed at cheap tiers rubber-stamping specifications.
- **Decision** (operator, 2026-10-19): Replace the blanket ban with a tier-aware rule, applied identically in `scripts/semantic_checker.py` (`is_accepted_auditor_model()`, used by both `run_cli_semantic_audit()` and `validate_semantic_traceability()`) and in the `scripts/spec-gate.py` dispatch guard: a model is rejected when its lowercase name contains `flash` and does not contain `high`. `gemini-3.8-flash-high` is an approved auditor; bare `flash`, `flash_lite`, Flash Medium and Flash Low remain rejected. The default CLI audit model (`SPEC_CHECKER_AGENT_MODEL`) changes from `claude-opus-4-6` to `gemini-3.8-flash-high`.
- **Consequences**: Flash High receipts now validate and Flash High auditor dispatches are allowed, while sub-High Flash tiers still cannot attest a specification. Opus-class models remain approved wherever they are available.
- **Addresses**: `REQ-016`, `REQ-017`

