# Architectural Design: Codebase Simplification & Parser Unification

- **Feature ID**: `2026-10-19-simplification-and-deduplication`
- **Status**: `Planning`
- **Addresses**: `REQ-009`, `REQ-010`, `REQ-011`, `REQ-012`

## 1. `scripts/spec_checker.py` Simplification (`REQ-009`)

### 1.1 `parse_specs_index_text(content: str) -> List[Dict[str, str]]`
- Moves the row-splitting and 6-column validation loop out of `parse_specs_index(index_path)` into `parse_specs_index_text(content: str)`.
- `parse_specs_index(index_path)` becomes:
  ```python
  def parse_specs_index(index_path: Union[Path, str]) -> List[Dict[str, str]]:
      path = Path(index_path)
      if not path.exists():
          raise FileNotFoundError(f"Index file not found: {path}")
      return parse_specs_index_text(path.read_text(encoding="utf-8"))
  ```

### 1.2 `resolve_package_dir(root: Path, specs_dir: Path, feat_id: str, spec_path_str: str) -> Tuple[Optional[Path], Optional[Dict[str, Any]]]`
- Extracts lines `274–337` of `verify_active_specification()` into a dedicated helper that validates `feat_id` characters, resolves candidate directories (`specs_dir / feat_id`, `specs_dir / spec_path_str`, `root / spec_path_str`), verifies `is_relative_to(root)`, and returns `(pkg_dir, error_dict)`.
- Reduces `verify_active_specification()` from 238 lines to ~115 lines and keeps `spec_checker.py` under 450 lines.

---

## 2. `scripts/spec-gate.py` Simplification & Hardening (`REQ-010`, `REQ-011`)

### 2.1 Component-Aware `is_allowed_runtime_artifact_path(target_path: Path) -> bool` (`REQ-011`)
```python
def is_allowed_runtime_artifact_path(target_path: Path) -> bool:
    """Check if path has contiguous (.gemini, antigravity, brain|scratch) parts or matches AGY_RUNTIME_ARTIFACT_DIR."""
    parts = target_path.parts
    for i in range(len(parts) - 2):
        if parts[i] == ".gemini" and parts[i + 1] == "antigravity" and parts[i + 2] in ("brain", "scratch"):
            return True

    custom_artifact_dir = os.environ.get("AGY_RUNTIME_ARTIFACT_DIR")
    if custom_artifact_dir and custom_artifact_dir.strip():
        try:
            custom_path = Path(custom_artifact_dir).resolve()
            if target_path.resolve().is_relative_to(custom_path):
                return True
        except (ValueError, RuntimeError):
            pass

    return False
```

### 2.2 Unified `is_unauthorized_status_promotion()` (`REQ-010`)
- When `"TargetContent"` in `args`:
  - If not `target_c` or `target_c not in disk_text`, return `True, "Spec Gate Rejection: TargetContent not found in docs/specs/INDEX.md"`.
- When `"ReplacementChunks"` in `args`:
  - If any `chunk.get("TargetContent")` is empty or not in `projected_text`, return `True, "Spec Gate Rejection: ReplacementChunk TargetContent not found in docs/specs/INDEX.md"`.
- Parse `projected_text` via `checker.parse_specs_index_text(projected_text)`:
  - If `parse_specs_index_text` raises `ValueError`, return `True` (reject malformed edit to `INDEX.md`).
  - If any record in `projected_records` has `checker.normalize_status(r["status"]) in checker.EXECUTION_STATUSES` and `r["feature_id"] not in existing_approved`, return `True` with the self-approval rejection message.

---

## 3. Unit Tests & Sub-450-Line Test Modularization (`REQ-012`, `REQ-013`, `REQ-015`)
- `scripts/spec_checker.py`: Clean single signature `resolve_package_dir(spec: Dict[str, str], root: Union[Path, str], specs_dir: Optional[Union[Path, str]] = None) -> Tuple[Optional[Path], Optional[str]]`.
- `tests/test_spec_checker.py` (< 450 lines): Test `parse_specs_index_text()` and single-signature `resolve_package_dir()`.
- `tests/test_spec_gate.py` (< 400 lines) & `tests/test_spec_gate_security.py` (< 400 lines): Split security, spoofing, symlink escape, multi-workspace resolution, and `INDEX.md` approval tests into `test_spec_gate_security.py`.

---

## 4. `hooks.json` Schema, `workspacePaths` Resolution & Transcript Approval (`REQ-014`)
- `hooks.json`:
  ```json
  {
    "spec-gate-plugin": {
      "PreToolUse": [
        {
          "matcher": "^(?:default_api:|client:)?(invoke_subagent|write_to_file|replace_file_content|multi_replace_file_content)$",
          "hooks": [
            {
              "type": "command",
              "command": "/usr/bin/env python3 ./scripts/spec-gate.py",
              "timeout": 5
            }
          ]
        }
      ]
    }
  }
  ```
- `get_candidate_workspaces(payload: Dict[str, Any]) -> List[Path]`:
  - Collects paths from `AGY_ACTIVE_WORKSPACE`, `payload.get("cwd")`, `payload.get("workspacePaths")` (list of strings), or falls back to `[os.getcwd()]`.
- `resolve_target_workspace(resolved_target: Path, candidate_workspaces: List[Path]) -> Optional[Path]`:
  - First checks if `resolved_target.is_relative_to(ws)` for any `ws` in `candidate_workspaces`.
  - Otherwise, walks `for parent in [resolved_target] + list(resolved_target.parents):` and if `(parent / "docs" / "specs").is_dir()` or `(parent / ".git").exists()`, returns `parent`.
  - Returns `None` if no enclosing workspace root is found.
- `has_recent_user_approval(payload: Dict[str, Any]) -> bool`:
  - Reads `transcriptPath` from `payload`. Scans JSONL lines for the last step where `source == "USER_EXPLICIT"` and `type == "USER_INPUT"`.
  - Strips `<ADDITIONAL_METADATA>...</ADDITIONAL_METADATA>` and checks if `re.search(r"\b(proceed|approve|approved|yes|lgtm)\b", clean_lower)` or `"the user has approved this document" in clean_lower` (and `"/plan" not in clean_lower`).

---

## 5. Content-Hashed Opus Semantic Traceability (`REQ-016`, `REQ-017`)

### 5.1 Receipt Schema (`<package_dir>/traceability_audit.json`)
```json
{
  "spec_hash": "<sha256 hex of spec.md + decisions.md + design.md + tasks.md>",
  "evidence_hash": "<optional sha256 hex including verification.md>",
  "auditor_model": "claude-opus-4-6",
  "verdict": "PASS",
  "requirements_evaluated": {
    "REQ-009": {
      "design_aligned": true,
      "design_rationale": "Section 1.1 and 1.2 define parse_specs_index_text() and resolve_package_dir().",
      "tasks_actionable": true,
      "tasks_rationale": "Task 1 specifies exact function extraction and line-count bounds.",
      "decisions_consistent": true,
      "evidence_verified": true,
      "evidence_rationale": "verification.md records 44/44 passing unit tests covering REQ-009."
    }
  }
}
```

### 5.2 `spec_checker.py` Functions (or `scripts/semantic_checker.py` helper imported by `spec_checker.py` to keep all files `< 450` lines)
- `compute_spec_package_hash(package_dir: Path, include_verification: bool = False) -> str`:
  - Hashes `<filename>\n<normalized_content>\n` for `["spec.md", "decisions.md", "design.md", "tasks.md"]` (+ `["verification.md"]` if `include_verification=True`).
- `validate_semantic_traceability(package_dir: Path, verify_evidence: bool = False, run_agent: bool = False) -> Tuple[bool, str]`:
  - If `run_agent=True` and receipt is missing/stale, invokes `SPEC_CHECKER_AGENT_CMD` or WorkBuddy CLI (`cbc`/`codebuddy -p --model <opus/primary-model> --output-format json`) with the spec package contents to generate `traceability_audit.json`.
  - Verifies `traceability_audit.json` exists, `verdict == "PASS"`, `auditor_model` passes the tier-aware auditor policy (rejected when its lowercase name contains `flash` without `high`; Opus-class and Flash High approved, per ADR-012), `spec_hash` matches disk (and `evidence_hash` matches disk when `verify_evidence=True`), and every declared `REQ-xxx` in `spec.md` has `design_aligned: true`, `tasks_actionable: true`, `decisions_consistent: true` (and `evidence_verified: true` when `verify_evidence=True`) with non-empty rationales.
- Enforce in `spec-gate.py`:
  - When `is_unauthorized_status_promotion()` detects a transition into `EXECUTION_STATUSES` (`Approved`, `In-Progress`, `Active`), resolve each promoted feature's `pkg_dir` via `checker.resolve_package_dir()` and call `checker.validate_semantic_traceability(pkg_dir, verify_evidence=False)`. If invalid, deny promotion even if user approval is present.
  - In `evaluate_spec_gate()`, allow subagents with `TypeName == "traceability-auditor"` or `Role.lower() == "traceability auditor"` during planning, but deny if `Model` names a Flash tier below High (contains `flash` without `high`, e.g. `"flash"`, `"flash_lite"`, `*-flash-medium`, `*-flash-low`).

