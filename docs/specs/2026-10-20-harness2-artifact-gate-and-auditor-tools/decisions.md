# Architectural Decision Records: Harness² Referenced Artifact Gate & Auditor Tool Permissions

## ADR-015: Grant `read_file`, `view_file`, `write_file`, and `write_to_file` to `traceability-auditor` (`REQ-023`)
- **Status**: Accepted
- **Context**: `agents/traceability-auditor.md` previously restricted `tools` to `[write_to_file]`, preventing the subagent from reading `spec.md`, `decisions.md`, `design.md`, `tasks.md`, and `verification.md` directly from disk.
- **Decision**: Expand `tools` in `agents/traceability-auditor.md` to `[read_file, view_file, write_file, write_to_file]`.

## ADR-016: Verify Referenced `scripts/*.py` and `tests/*.py` Artifacts in `verification.md` (`REQ-024`)
- **Status**: Accepted
- **Context**: Previously, `--verify-evidence` checked that `verification.md` cited `REQ-xxx` IDs and contained a code block or test metric, but did not check whether test/script files cited in `verification.md` actually existed in the workspace or compiled cleanly.
- **Decision**: Add `check_referenced_artifacts(spec_dir, repo_root)` to `scripts/spec_checker.py` (invoked when `verify_evidence=True` and `repo_root` can be resolved from `spec_dir.parent.parent.parent`) to verify existence and Python syntax compilation of all cited `(?:scripts|tests)/[A-Za-z0-9_.\-/]+\.py` paths.

## ADR-017: Domain-Prefixed Requirement IDs & Global `~/.gemini/config/` Gate Allowance (`REQ-025`, `REQ-026`)
- **Status**: Accepted
- **Context**: `REQ_ID_PATTERN` previously matched only `(?:REQ|FLOW|ALIGN)-\d+`, rejecting domain-prefixed requirement IDs (`REQ-AE-001`, `REQ-DSL-001`, `REQ-TOC-1`) in `attention-guard` and `agent-translator`. Additionally, `spec-gate.py` blocked file edits to non-git global configuration directories under `~/.gemini/config/rules/`.
- **Decision**: Expand `REQ_ID_PATTERN` to `r"\b(?:REQ|FLOW|ALIGN)-(?:[A-Z0-9]+-)*\d+\b"` in `scripts/spec_checker.py`, and allow `.gemini/config/{rules,scripts,skills}` and `.gemini/config/hooks.json` in `is_allowed_runtime_artifact_path()` in `scripts/spec-gate.py`.


## ADR-018: `/goal` Autonomous Mode & Antigravity 2.0 Tool Schema Parity in `spec-gate.py` (`REQ-027`)
- **Status**: Accepted
- **Context**: `RULE[explicit-approval]` specifies that `/goal` authorizes autonomous execution without intermediate approval stops, and Antigravity 2.0 uses `write_file`/`edit_file` (`Path`) and flat `invoke_subagent` arguments.
- **Decision**: Update `has_recent_user_approval()`, `FILE_MUTATION_TOOLS`, target path extraction, and subagent normalization in `scripts/spec-gate.py` to support `/goal` and Antigravity 2.0 tool schemas.
