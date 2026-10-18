# Architectural Design: True Spec-Driven Enforcement & Traceability

- **Feature ID**: `2026-10-18-true-spec-driven-enforcement`
- **Status**: `Approved`
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
                    │   1. Missing TargetFile arg?                 │──Yes──▶ DENY (Fail-closed)
                    │   2. Write outside workspace or docs/specs/? │──Yes──▶ ALLOW (Brain/Specs)
                    │   3. Mutating subagent / tool?               │──No───▶ ALLOW (Read-only)
                    └──────────────────────┬───────────────────────┘
                                      │ Yes (Requires Gate)
                                      ▼
                    ┌──────────────────────────────────────────────┐
                    │              spec_checker.py                 │
                    │   - No docs/specs directory?                 │──Yes──▶ ALLOW (Opt-in)
                    │   - Normalize statuses in INDEX.md           │
                    │   - Filter EXECUTION_STATUSES                │
                    │   - Verify path containment on all candidates│
                    │   - Validate 4 core non-empty documents      │
                    │   - Verify REQ-\d+ cross-document traceability│
                    └──────────────────────┬───────────────────────┘
                                      │
                        ┌─────────────┴─────────────┐
                        ▼ Valid                     ▼ Invalid / Unapproved
                   [ ALLOW ]                   [ DENY + Diagnostic ]
```

## 2. Component Design

### 2.1 `scripts/spec_checker.py` (Addresses: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-006`)

#### Constants & Status Normalization (`REQ-001`, `REQ-002`)
```python
REQ_PATTERN = re.compile(r"\b(REQ-\d+|FLOW-\d+|ALIGN-\d+)\b")
PLACEHOLDER_REQS = {"REQ-XXX", "REQ-xxx"}

PLANNING_STATUSES = {"draft", "planning", "review"}
EXECUTION_STATUSES = {"approved", "in-progress", "active"}
TERMINAL_STATUSES = {"completed", "implemented", "done", "abandoned", "superseded"}
ACTIVE_STATUSES = EXECUTION_STATUSES | PLANNING_STATUSES


def normalize_status(raw: str) -> str:
    """Normalize status string to lowercase hyphenated format."""
    return raw.strip().lower().replace(" ", "-").replace("_", "-")
```

#### Escaped-Pipe Safe Table Parser (`REQ-003`)
Update `parse_specs_index(index_path)`:
- Split table rows using `re.split(r"(?<!\\)\|", trimmed[1:-1])`.
- Unescape `\|` to `|` in each stripped cell: `[p.replace(r"\|", "|").strip() for p in raw_parts]`.
- Extract `feature_id`, `title`, `status`, `req_range`, `key_decisions`, `spec_path`.

#### Requirement ID Extraction & Traceability Validation (`REQ-001`, `REQ-003`)
```python
def extract_requirement_ids(text: str) -> List[str]:
    """Extract sorted, unique requirement IDs, excluding placeholders."""
    matches = set(REQ_PATTERN.findall(text))
    filtered = {m for m in matches if m not in PLACEHOLDER_REQS}
    return sorted(list(filtered))
```

Update `validate_spec_package(package_dir: Union[Path, str], verify_evidence: bool = False) -> Tuple[bool, str]`:
1. Check `pkg.exists() and pkg.is_dir()`.
2. Require core files: `required_files = ["spec.md", "decisions.md", "design.md", "tasks.md"]` (`REQ-003`).
3. If `verify_evidence` is `True`, append `"verification.md"` to `required_files` (`REQ-001`).
4. For each required file:
   - Verify `target.exists() and target.is_file()`.
   - Read UTF-8 text and check `len(content.strip()) > 0` (rejects 0-byte and whitespace-only files, `REQ-003`).
5. Extract `spec_reqs = extract_requirement_ids(contents["spec.md"])`:
   - If `not spec_reqs`, return `False, "spec.md does not contain any valid requirement ID (REQ-\\d+, FLOW-\\d+, ALIGN-\\d+)"`.
6. Verify traceability across `design.md` and `tasks.md` (and `verification.md` when `verify_evidence=True`) (`REQ-001`):
   - For each target doc in `["design.md", "tasks.md"]` (+ `["verification.md"]` if `verify_evidence`):
     - Compute `doc_reqs = set(extract_requirement_ids(contents[doc]))`.
     - Compute `missing = [r for r in spec_reqs if r not in doc_reqs]`.
     - If `missing`: return `False, f"{doc} is missing requirement IDs declared in spec.md: {', '.join(missing)}"`.
7. Verify `decisions.md` contains at least one `ADR-\d+` or one declared requirement ID from `spec_reqs`.

#### Workspace Verification & Path Containment (`REQ-002`, `REQ-003`, `REQ-006`)
Update `verify_active_specification(workspace_root: Union[Path, str], require_approved: bool = True, feature_id: Optional[str] = None, verify_evidence: bool = False) -> Dict[str, Any]`:
1. Resolve `root = Path(workspace_root).resolve()` and `specs_dir = root / "docs" / "specs"`.
2. If `not specs_dir.exists() or not specs_dir.is_dir()`: return `{"status": "no_spec_framework", "valid": True, "reason": "No docs/specs directory in workspace"}` (`REQ-002`).
3. Parse `INDEX.md`. If `feature_id` is provided (`REQ-006`), filter `records` to `r["feature_id"] == feature_id`; if not found, return `{"status": "feature_not_found", "valid": False, "reason": f"Feature '{feature_id}' not found in docs/specs/INDEX.md"}`.
4. Partition candidate records using `normalize_status(r["status"])`:
   - `exec_specs`: records with normalized status in `EXECUTION_STATUSES`
   - `plan_specs`: records with normalized status in `PLANNING_STATUSES`
5. If `require_approved` is `True`:
   - If `not exec_specs`:
     - If `plan_specs`: return `{"status": "unapproved_spec", "valid": False, "reason": "Specification exists in planning/draft status but is not yet approved (status must be Approved, In-Progress, or Active)."}` (`REQ-002`).
     - Else: return `{"status": "no_active_spec", "valid": False, "reason": "No active specification found in docs/specs/INDEX.md"}`.
   - Target list to validate is `exec_specs` (`REQ-006`).
6. If `require_approved` is `False`:
   - Target list to validate is `exec_specs + plan_specs`.
7. For each spec in the target list:
   - Path traversal guard: Check `feat_id` for path separators (`/`, `\\`, `..`). If present, return `{"status": "invalid_path", "valid": False, "reason": f"Feature ID '{feat_id}' contains invalid path characters"}`.
   - Resolve candidate package directories (`specs_dir / feat_id`, `specs_dir / spec_path`, `root / spec_path`).
   - Verify all candidates via `cand.resolve().is_relative_to(root)` (`REQ-003`). If outside, return `status: "invalid_path"`.
   - Validate package via `validate_spec_package(pkg_dir, verify_evidence=verify_evidence)`.
8. In multi-spec mode (`feature_id is None` and `require_approved is True`, `REQ-006`):
   - Collect `valid_features` and `errors`.
   - If `len(valid_features) >= 1`: return `{"status": "valid", "valid": True, "active_features": valid_features, "warnings": errors}`.
   - Otherwise return the first failure in `errors`.

#### CLI Arguments & Exit Codes (`REQ-002`, `REQ-006`)
- `--feature`: Validate a specific `feature_id`.
- `--allow-planning`: Set `require_approved=False`.
- `--verify-evidence`: Set `verify_evidence=True`.
- `--workspace`: Specify target workspace root.
- `--json`: Output structured JSON report.
- `--quiet`: Suppress diagnostic text.
- **Exit Codes**:
  - `0`: Valid specification package (`valid: True`).
  - `1`: Invalid or unapproved specification (`valid: False`).
  - `2`: Internal error or corrupt index (`status: "corrupt_index"` / `"error"`).

---

### 2.2 `hooks.json` & `scripts/spec-gate.py` (Addresses: `REQ-002`, `REQ-004`, `REQ-005`)

#### Hook Registration (`hooks.json`, `REQ-004`)
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$",
        "command": "python3 ${PLUGIN_ROOT}/scripts/spec-gate.py"
      }
    ]
  }
}
```

#### Subagent & Direct Tool Evaluation (`scripts/spec-gate.py`, `REQ-004`, `REQ-005`)
1. Purge legacy domain code: Remove `TRANSLATION_TYPES`, `"runs/"` prompt exemptions, `EXEMPT_TYPES`, and `AGY_ATTENTION_GUARD_OBSERVATION_MODE` (`REQ-005`).
2. Tool name sets:
   - `SUBAGENT_TOOLS = {"invoke_subagent", "default_api:invoke_subagent", "client:invoke_subagent"}`
   - `FILE_MUTATION_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content", "client:write_to_file", "client:replace_file_content", "client:multi_replace_file_content", "default_api:write_to_file", "default_api:replace_file_content", "default_api:multi_replace_file_content"}`
3. Subagent evaluation:
   - `MUTATION_KEYWORDS = {"implement", "modify", "compiler", "executor", "builder", "patch", "write_to_file", "replace_file_content"}`. Generic `"code"` is omitted.
   - Keyword matching uses regex word boundaries: `re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE)` to prevent false collisions on `"codebase researcher"`.
   - Check `is_mutating_subagent(sa)` **first**. If `True`, set `requires_gate = True`.
   - If not mutating, check `is_exempt_subagent(sa)` (`TypeName == "research"` or `Role in EXEMPT_ROLES`).
   - If neither mutating nor exempt, fail closed (`requires_gate = True`).
4. Direct file mutation evaluation:
   - Extract raw target path from `args.get("TargetFile") or args.get("target_file") or args.get("file_path") or args.get("path")`.
   - If missing or empty: return `{"decision": "deny", "reason": "Spec Gate Rejection: Missing target file path in mutation tool call"}`.
   - Resolve path relative to `workspace_root`:
     ```python
     target = Path(raw_path)
     if not target.is_absolute():
         target = Path(workspace_root) / target
     resolved_target = target.resolve()
     workspace_path = Path(workspace_root).resolve()
     ```
   - **External artifact exemption**: If `not resolved_target.is_relative_to(workspace_path)`, return `{"decision": "allow"}`.
   - **Spec authoring exemption**: If `resolved_target.is_relative_to(workspace_path / "docs" / "specs")`, return `{"decision": "allow"}`.
   - Otherwise set `requires_gate = True`.
5. When `requires_gate` is `True`, invoke `checker.verify_active_specification(workspace_root, require_approved=True)`. If `valid: False`, return `decision: "deny"` with diagnostic details.

---

### 2.3 `rules/spec-standard.md` & `skills/spec-standard/SKILL.md` (Addresses: `REQ-007`)
- Update `skills/spec-standard/SKILL.md` Section 2 (*Scaling Switches*) so that `spec.md`, `decisions.md`, `design.md`, and `tasks.md` form the mandatory planning baseline verified by `spec_checker.py`, while `verification.md` is required upon Phase 2 verification.
- Document standalone fallbacks in both documents when `/grill-me` or `/plan` are absent.

---

### 2.4 `tests/test_spec_checker.py` & `tests/test_spec_gate.py` (Addresses: `REQ-008`)
- Remove external repo path references (`../ai-review-plugin`) and replace with isolated temporary fixture directories.
- Unit test coverage for `AC-001-1` through `AC-008-3`.
