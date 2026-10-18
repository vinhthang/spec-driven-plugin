# Architectural Design: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Implemented`
- **Addresses**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`, `REQ-008`

## 1. System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        IDE / Agent Runtime (PreToolUse)                    │
└─────────────────────────────────────┬──────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┴─────────────────────────────┐
        ▼                                                           ▼
┌───────────────────────────────┐           ┌───────────────────────────────┐
│   Subagent Dispatch           │           │   Direct File Mutation Tools  │
│   - invoke_subagent           │           │   - write_to_file             │
│   - default_api:invoke_...    │           │   - replace_file_content      │
└───────────────┬───────────────┘           │   - multi_replace_file_content│
                │                           └───────────────┬───────────────┘
                └─────────────────────┬─────────────────────┘
                                      ▼
                    ┌──────────────────────────────────────────────┐
                    │          hooks.json -> spec-gate.py          │
                    │   1. Missing TargetFile or symlink escape?   │──Yes──▶ DENY (Fail-closed)
                    │   2. Allowed runtime brain/scratch artifact? │──Yes──▶ ALLOW
                    │   3. Write to docs/specs/?                   │
                    │      - Self-promoting INDEX.md to Approved?  │──Yes──▶ DENY (Self-approval)
                    │      - Otherwise                             │──Yes──▶ ALLOW (Spec authoring)
                    │   4. Mutating subagent / workspace tool?     │──No───▶ ALLOW (Read-only)
                    └──────────────────────┬───────────────────────┘
                                           │ Yes (Requires Gate)
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │              spec_checker.py                 │
                    │   - No docs/specs directory?                 │──Yes──▶ ALLOW (Opt-in)
                    │   - Strictly parse 6-column INDEX.md         │
                    │   - Filter EXECUTION / PLANNING / TERMINAL   │
                    │   - Verify path containment on all candidates│
                    │   - Validate 4 core non-empty documents      │
                    │   - Verify declared REQ-\d+ traceability     │
                    └──────────────────────┬───────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼ Valid                               ▼ Invalid / Unapproved
                   [ ALLOW ]                             [ DENY + Diagnostic ]
```

## 2. Component Design

### 2.1 `scripts/spec_checker.py` (Addresses: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-006`)

#### Constants & Status Normalization (`REQ-001`, `REQ-002`)
```python
REQ_PATTERN = re.compile(r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b")
DECLARED_REQ_LINE_PATTERN = re.compile(
    r"^(?:\s*#{1,6}\s+.*?\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"
    r"|\s*[-*+]\s+(?:\*\*|`)*(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b"
    r"|\s*\|\s*`?(REQ-\d+|FLOW-\d+|ALIGN-\d+)`?\s*\|)",
    re.MULTILINE,
)
PLACEHOLDER_REQS = {"REQ-XXX", "REQ-xxx"}

PLANNING_STATUSES = {"draft", "planning", "review"}
EXECUTION_STATUSES = {"approved", "in-progress", "active"}
VERIFIABLE_TERMINAL_STATUSES = {"completed", "implemented", "done"}
TERMINAL_STATUSES = VERIFIABLE_TERMINAL_STATUSES | {"abandoned", "superseded"}
ACTIVE_STATUSES = EXECUTION_STATUSES | PLANNING_STATUSES
```

#### Strict 6-Column Escaped-Pipe Table Parser (`REQ-003` / `AC-003-4`)
In `parse_specs_index(index_path)`:
- Split table rows using `re.split(r"(?<!\\)\|", trimmed[1:-1])`.
- Unescape `\|` to `|` in each stripped cell: `[p.replace(r"\|", "|").strip() for p in raw_parts]`.
- Reject any row where `len(parts) != 6`:
  ```python
  if len(parts) != 6:
      raise ValueError(
          f"Malformed table row at line {line_idx} (expected 6 columns, got {len(parts)}): {line}"
      )
  ```

#### Declared Requirement ID Extraction & Strict Traceability (`REQ-001` / `AC-001-1`, `AC-001-2`)
- Add `extract_declared_requirement_ids(spec_text: str) -> List[str]`:
  - Scans `spec_text` using `DECLARED_REQ_LINE_PATTERN` to collect IDs declared in Markdown headings (`### \`REQ-001\`: ...`), bullet lead-ins (`- **REQ-001**: ...` or `- REQ-001: ...`), or table first columns (`| \`REQ-001\` |`).
  - If at least one structured declaration is found, returns those sorted unique IDs (excluding `PLACEHOLDER_REQS`).
  - If no structured declaration is found (e.g. minimal single-line test fixtures), falls back to `extract_requirement_ids(spec_text)`.
- In `validate_spec_package(package_dir, verify_evidence=False)`:
  - Extract `spec_reqs = extract_declared_requirement_ids(contents["spec.md"])`.
  - **Remove the undocumented `Governing Specification:.*spec\.md` bypass**: every ID in `spec_reqs` MUST appear in `extract_requirement_ids(contents["design.md"])` and `extract_requirement_ids(contents["tasks.md"])` (and `extract_requirement_ids(contents["verification.md"])` when `verify_evidence=True`).

#### Terminal Status & Feature-Scoped Verification (`REQ-001` / `AC-001-3`, `REQ-006` / `AC-006-2`, `AC-006-3`)
In `verify_active_specification(workspace_root, require_approved=True, feature_id=None, verify_evidence=False)`:
1. Partition `records` into:
   - `exec_specs`: normalized status in `EXECUTION_STATUSES`
   - `plan_specs`: normalized status in `PLANNING_STATUSES`
   - `verifiable_term_specs`: normalized status in `VERIFIABLE_TERMINAL_STATUSES` (`{"completed", "implemented", "done"}`)
2. Determine `target_specs`:
   - Start with `target_specs = exec_specs + plan_specs`.
   - If `feature_id is not None` and `not target_specs` and `verifiable_term_specs`:
     - Include `verifiable_term_specs` in `target_specs` (`AC-006-2`).
   - Else if `verify_evidence` is `True` and `not target_specs` and `verifiable_term_specs`:
     - Include `verifiable_term_specs` in `target_specs` (`AC-006-3`).
3. During package validation for each `spec` in `target_specs`:
   - Compute `norm_status = normalize_status(spec.get("status", ""))`.
   - Set `effective_verify_evidence = verify_evidence or (norm_status in VERIFIABLE_TERMINAL_STATUSES)` (`AC-001-3`).
   - Treat `verifiable_term_specs` as execution-equivalent (`is_exec = norm_status in EXECUTION_STATUSES or (norm_status in VERIFIABLE_TERMINAL_STATUSES and (feature_id is not None or verify_evidence))`) ONLY when `feature_id is not None` or `verify_evidence is True` (so normal `spec-gate.py` calls with `require_approved=True, feature_id=None, verify_evidence=False` continue to reject workspaces where all specs are `Completed`/`Implemented`).

---

### 2.2 `hooks.json` & `scripts/spec-gate.py` (Addresses: `REQ-002`, `REQ-004`, `REQ-005`)

#### Workspace Root Precedence & Symlink Containment (`REQ-004` / `AC-004-2`)
1. Resolve `workspace_root`:
   ```python
   workspace_root = os.environ.get("AGY_ACTIVE_WORKSPACE") or payload.get("cwd") or os.getcwd()
   workspace_path = Path(workspace_root).resolve()
   ```
2. Resolve lexical and physical target paths without symlink escape:
   ```python
   raw_target = Path(raw_path)
   lexical_target = raw_target if raw_target.is_absolute() else (workspace_path / raw_target)
   lexical_abs = Path(os.path.abspath(str(lexical_target)))
   resolved_target = lexical_target.resolve()

   # Block in-workspace symlinks that resolve outside workspace_path
   if lexical_abs.is_relative_to(workspace_path) and not resolved_target.is_relative_to(workspace_path):
       return {
           "decision": "deny",
           "reason": f"Spec Gate Rejection: Symlink target '{raw_path}' resolves outside workspace root ('{resolved_target}')",
       }
   ```
3. Narrow `is_allowed_runtime_artifact_path(target_path: Path) -> bool` (`AC-004-2.4`):
   - Allow paths containing `.gemini/antigravity/brain` or `.gemini/antigravity/scratch`.
   - Allow paths relative to `Path(os.environ["AGY_RUNTIME_ARTIFACT_DIR"]).resolve()` when `AGY_RUNTIME_ARTIFACT_DIR` is set and non-empty.
   - Do **not** blanket-allow `/tmp` or `tempfile.gettempdir()`.

#### Mechanical Self-Approval Guard on `docs/specs/INDEX.md` (`REQ-004` / `AC-004-4`)
Add helper `is_unauthorized_status_promotion(index_path: Path, args: Dict[str, Any], checker: Any) -> Tuple[bool, str]`:
1. If `os.environ.get("SPEC_GATE_ALLOW_APPROVAL") == "1"`, return `False, ""`.
2. Determine existing execution-authorized feature IDs on disk:
   - If `index_path.exists()`, parse existing rows via `checker.parse_specs_index(index_path)` (ignoring parse errors if currently corrupt) and collect `existing_approved = {r["feature_id"] for r in rows if checker.normalize_status(r.get("status", "")) in checker.EXECUTION_STATUSES}`.
   - If `not index_path.exists()`, `existing_approved = set()`.
3. Reconstruct or inspect candidate text from `args`:
   - Collect strings from `args.get("Content")`, `args.get("CodeContent")`, `args.get("ReplacementContent")`, and any `chunk.get("ReplacementContent")` in `args.get("ReplacementChunks", [])`.
   - Parse any Markdown table rows in the candidate text that have 6 columns.
   - If any row has `checker.normalize_status(status) in checker.EXECUTION_STATUSES` and its `feature_id` is not in `existing_approved`:
     - Return `True, f"Spec Gate Rejection: Autonomous self-approval of feature '{feature_id}' to status '{status}' in docs/specs/INDEX.md is forbidden. Register as Draft/Planning and ask the user to approve."`
4. Invoke this check whenever `resolved_target == (workspace_path / "docs" / "specs" / "INDEX.md")`.

---

### 2.3 `rules/spec-standard.md` & `skills/spec-standard/SKILL.md` (Addresses: `REQ-007`)
- Document in `rules/spec-standard.md` under `<scope>` that in repositories with `docs/specs/` enabled, `spec-gate.py` mechanically gates all file mutations outside `docs/specs/` until an active specification is in `Approved`, `In-Progress`, or `Active` status.

### 2.4 `tests/test_spec_checker.py` & `tests/test_spec_gate.py` (Addresses: `REQ-008`)
- Add unit tests for:
  - `test_declared_requirement_ids_ignores_prose_mentions`: `spec.md` mentioning `REQ-099` in prose background while declaring `### REQ-001` only requires `REQ-001` in `design.md` and `tasks.md`.
  - `test_governing_spec_link_does_not_bypass_design_traceability`: `design.md` with `Governing Specification: spec.md` still fails if `REQ-001` is missing.
  - `test_parse_specs_index_extra_columns_raises`: 7-column row raises `ValueError` / `corrupt_index`.
  - `test_verify_terminal_implemented_spec_with_feature_and_verify_evidence`: `Implemented` status in `INDEX.md` passes when `--verify-evidence` or `--feature` is used (with valid `verification.md`), and still blocks `require_approved=True` when `verify_evidence=False, feature_id=None`.
  - `test_self_approval_in_index_md_denied`: `write_to_file` or `replace_file_content` writing `Approved` for a new or `Planning` feature into `docs/specs/INDEX.md` is denied unless `SPEC_GATE_ALLOW_APPROVAL=1` or already `Approved` on disk.
  - `test_workspace_symlink_escape_denied`: symlink inside workspace pointing to `.gemini/antigravity/brain/evil.py` is denied.
