# Architectural Design: SDD Lifecycle Automation, Checkbox Hash Normalization & EARS Governance

- **Feature ID**: `2026-10-19-sdd-lifecycle-and-ears-evolution`
- **Status**: `Planning`
- **Addresses**: `REQ-018`, `REQ-019`, `REQ-020`, `REQ-021`, `REQ-022`

## 1. Checkbox Normalization in `scripts/semantic_checker.py` (`REQ-018`)

In `compute_spec_package_hash(package_dir, include_verification=False)`:
```python
norm_text = text.replace("\r\n", "\n").strip()
if fname == "tasks.md":
    norm_text = re.sub(r"^(\s*[-*+]\s+)\[[xX]\]", r"\1[ ]", norm_text, flags=re.MULTILINE)
hasher.update(f"{fname}\n{norm_text}\n".encode("utf-8"))
```

---

## 2. Lifecycle & Quality Module: `scripts/spec_lifecycle.py` (`REQ-019`, `REQ-020`, `REQ-022`)

### 2.1 `check_ambiguity_markers(content: str, filename: str) -> Optional[str]` (`REQ-022`)
- Strips fenced code blocks (` ```[\s\S]*?``` `) and inline code spans (`` `[^`\n]*` ``) and double/single-quoted literals (`"[^"\n]*"`, `'[^'\n]*'`) so specifications that discuss `TODO` tokens in code are never falsely rejected.
- Searches the remaining prose for `\[NEEDS CLARIFICATION[^\]]*\]` or `\b(TODO|TBD|FIXME)\s*:`.
- Returns a diagnostic error string if matched, or `None` if clean.

### 2.2 `validate_task_completion(package_dir: Union[Path, str]) -> Tuple[bool, str]` (`REQ-019`)
- Reads `<package_dir>/tasks.md` (stripping fenced code blocks).
- Counts unchecked items `^\s*[-*+]\s+\[\s\]\s+` and checked items `^\s*[-*+]\s+\[[xX]\]\s+`.
- If `unchecked_count > 0`, returns `(False, f"tasks.md still has {unchecked_count} unchecked task(s) (- [ ])")`.
- If `checked_count == 0`, returns `(False, "tasks.md does not contain any completed task checkboxes (- [x])")`.
- Returns `(True, "")`.

### 2.3 `init_spec_package(workspace_root: Union[Path, str], feature_id: str, title: Optional[str] = None) -> Dict[str, Any]` (`REQ-020`)
- Validates `feature_id` (rejects `..`, `/`, `\`).
- Scans `docs/specs/INDEX.md` and `docs/specs/**/spec.md` + `decisions.md` for the highest `REQ-(\d+)` and `ADR-(\d+)` numbers, computing `next_req = f"REQ-{max_req + 1:03d}"` and `next_adr = f"ADR-{max_adr + 1:03d}"`.
- Creates `docs/specs/<feature_id>/` with EARS-formatted `spec.md`, `decisions.md`, `design.md`, and `tasks.md` referencing `next_req` and `next_adr`.
- Creates or appends a 6-column `Planning` row to `docs/specs/INDEX.md`.

### 2.4 `close_spec_package(workspace_root: Union[Path, str], feature_id: str) -> Dict[str, Any]` (`REQ-019`)
- Resolves `pkg_dir` for `feature_id` from `docs/specs/INDEX.md`.
- Verifies `validate_task_completion(pkg_dir)` and `validate_spec_package(pkg_dir, verify_evidence=True)`.
- Updates the feature's status cell in `docs/specs/INDEX.md` to `Implemented` (and updates `- **Status**:` in `spec.md` to `` `Implemented` ``).

---

## 3. `scripts/spec-gate.py` Enhancements (`REQ-019`, `REQ-021`)

### 3.1 `is_exempt_documentation_file(resolved_target: Path, target_ws: Path) -> bool` (`REQ-021`)
- Returns `True` if `resolved_target` is inside `target_ws`, has suffix `.md` or `.markdown`, and is either:
  - Located at workspace root with name in `{"readme.md", "changelog.md", "contributing.md"}` (case-insensitive), or
  - Relative to `target_ws / "docs"` (note: `docs/specs/INDEX.md` is checked by `is_unauthorized_status_promotion` before this exemption).
- Returns `False` for `rules/*.md`, `skills/**/*.md`, `agents/*.md`, and all non-markdown code/config files.

### 3.2 Terminal Status Verification in `is_unauthorized_status_promotion()` (`REQ-019`)
- When a feature row in `projected_records` transitions into `checker.VERIFIABLE_TERMINAL_STATUSES` (`implemented`, `completed`, `done`) from a non-terminal status:
  - Resolves `pkg_dir` via `checker.resolve_package_dir()`.
  - Calls `checker.validate_task_completion(pkg_dir)` and `checker.validate_spec_package(pkg_dir, verify_evidence=True)`.
  - If either fails, denies the edit to `docs/specs/INDEX.md` with a diagnostic message.
