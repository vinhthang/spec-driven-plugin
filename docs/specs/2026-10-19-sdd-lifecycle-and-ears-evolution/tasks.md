# Execution Tasks: SDD Lifecycle Automation, Checkbox Hash Normalization & EARS Governance

- **Feature ID**: `2026-10-19-sdd-lifecycle-and-ears-evolution`
- **Status**: `Planning`

## Implementation Checklist

- [ ] **Task 1: Normalize volatile `tasks.md` checkboxes in `scripts/semantic_checker.py`** (`REQ-018`)
  - [ ] Update `compute_spec_package_hash()` to normalize `- [x]` / `- [X]` to `- [ ]` in `tasks.md` before hashing (`AC-018-1`, `AC-018-2`).
- [ ] **Task 2: Create `scripts/spec_lifecycle.py` and integrate `--init`, `--close`, task completion, and ambiguity checks into `scripts/spec_checker.py`** (`REQ-019`, `REQ-020`, `REQ-022`)
  - [ ] Implement `check_ambiguity_markers()`, `validate_task_completion()`, `init_spec_package()`, and `close_spec_package()` in `scripts/spec_lifecycle.py` (< 220 lines) (`AC-019-1`, `AC-019-2`, `AC-020-1`, `AC-020-2`, `AC-022-1`).
  - [ ] Integrate `check_ambiguity_markers()` and CLI flags `--init <id>`, `--title <title>`, and `--close <id>` into `scripts/spec_checker.py` (< 445 lines) and synchronize `spec_checker.py`, `semantic_checker.py`, and `spec_lifecycle.py` to `ai-review-plugin/scripts/`.
- [ ] **Task 3: Update `scripts/spec-gate.py` for non-code documentation exemption and terminal status task-completion gating** (`REQ-019`, `REQ-021`)
  - [ ] Add `is_exempt_documentation_file()` for `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, and `docs/**/*.md` (`AC-021-1`).
  - [ ] Enforce `validate_task_completion()` and `validate_spec_package(..., verify_evidence=True)` when transitioning a feature to `Implemented`/`Completed`/`Done` in `docs/specs/INDEX.md` (`AC-019-3`).
- [ ] **Task 4: Update `skills/spec-standard/SKILL.md` with EARS notation & CLI lifecycle and add `tests/test_spec_lifecycle.py`** (`REQ-018` – `REQ-022`)
  - [ ] Document EARS syntax templates and `--init` / `--close` commands in `skills/spec-standard/SKILL.md` (`AC-022-2`).
  - [ ] Add comprehensive unit tests in `tests/test_spec_lifecycle.py` (< 350 lines), verify all `.py` files are `< 450` lines, run `rtk pytest -v` across `spec-driven-plugin` and `ai-review-plugin`, close prior completed specs using `--close`, and record verbatim outputs in `verification.md`.
