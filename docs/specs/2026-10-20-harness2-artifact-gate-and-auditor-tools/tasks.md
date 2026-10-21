# Tasks: Harness² Referenced Artifact Verification Gate & Traceability Auditor Tool Permissions

## Phase 1: Agent Frontmatter, Artifact Verification Gate & Ecosystem SDD Alignment

- [x] **Task 1 (`REQ-023`)**: Update `agents/traceability-auditor.md` frontmatter `tools` list to `[read_file, view_file, write_file, write_to_file]`.
- [x] **Task 2 (`REQ-024`)**: Implement `check_referenced_artifacts(spec_dir, repo_root)` in `scripts/spec_checker.py` and wire it into `validate_spec_package(..., verify_evidence=True)`.
- [x] **Task 3 (`REQ-025`, `REQ-026`)**: Expand `REQ_ID_PATTERN` in `scripts/spec_checker.py` to support domain-prefixed requirement IDs (`REQ-AE-001`, `REQ-DSL-001`) and allow `~/.gemini/config/{rules,scripts,skills,hooks.json}` in `scripts/spec-gate.py`.
- [x] **Task 4 (`REQ-023`–`REQ-026`)**: Add unit tests in `tests/test_spec_checker.py` and `tests/test_spec_gate.py` covering all requirements.

- [x] **Task 5 (`REQ-027`)**: Update `scripts/spec-gate.py` and `tests/test_spec_gate.py` for `/goal` autonomous approval recognition and Antigravity 2.0 `write_file`/`edit_file`/`Path`/flat `invoke_subagent` parity.
- [x] **Task 6 (`REQ-028`)**: Implement `extract_prompt_workspaces()` in `scripts/spec-gate.py` and add unit tests in `tests/test_spec_gate.py` for target repository resolution from absolute paths in `invoke_subagent` prompts.
