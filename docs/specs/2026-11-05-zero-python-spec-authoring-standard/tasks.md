# Execution Tasks: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- [x] **Task 1 (`REQ-034`, `AC-034-1`, `AC-034-2`)**:
  - Remove `hooks.json`, `scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, `agents/traceability-auditor.md`, `tests/*.py`, and all `__pycache__` / `.pyc` artifacts from `spec-driven-plugin`.
  - Document the retirement and migration table for legacy CLI/hook consumers (`spec_checker.py --init/--close`, `spec-gate.py`, `traceability_audit.json`) in `README.md` and `docs/specs/INDEX.md`.
- [x] **Task 2 (`REQ-035`, `AC-035-1`, `AC-035-2`)**:
  - Author `rules/spec-standard.md` and `skills/spec-standard/SKILL.md` defining the Normative Source (`spec.md`, `decisions.md`) vs. Derived Blueprint (`design.md`, `tasks.md`, `verification.md`) hierarchy, requiring written **Gate 1** (`decisions.md`) and per-AC **Gate 2** (`tasks.md`) self-validation tables, and blocking `In-Progress` (remaining in or reverting to `Planning`) if any Gate 1 or Gate 2 check fails or is omitted.
- [x] **Task 3 (`REQ-036`, `AC-036-1`, `AC-036-2`)**:
  - Define disjoint **In-Place Amendment** (`Planning`/`In-Progress`), **Whole-Spec Supersession** (`Supersedes` + `[NEW]`), and **Living-Spec Modification** (`Extends / Modifies` + per-ID `[MODIFIES]` / `[DEPRECATED]` + counterpart `REQ-xxx` heading and `INDEX.md` annotations) rules in `rules/spec-standard.md` and `skills/spec-standard/SKILL.md`.
  - Cascade `Status: Superseded` across `docs/specs/INDEX.md` and all 5 superseded specification packages (`2026-10-18` through `2026-10-30`, `REQ-001` – `REQ-033`, and all 25 historical ADR blocks `ADR-001` – `ADR-024`).
- [x] **Task 4 (`REQ-037`, `AC-037-1`, `AC-037-2`)**:
  - Synchronize the 6-state lifecycle (`Planning`, `In-Progress`, `In-Testing`, `Verified`, `Superseded`, `Abandoned`), self-contained human `"Proceed"` `Sign-off` recording, and the 3-Way Bug Decision Protocol (`Case 1: Implementation Bug`, `Case 2: Design/ADR Flaw`, `Case 3: Spec Gap/Flaw`) across `spec.md`, `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, and `README.md`.
  - Author and verify the `docs/specs/2026-11-05-zero-python-spec-authoring-standard/` specification package in `In-Testing` status.

---

## Gate 2: Derived File Self-Validation & Traceability Matrix (`design.md`, `tasks.md`, `verification.md`)

| Requirement ID | Acceptance Criteria | Governing ADR | Design Section (`design.md`) | Execution Task (`tasks.md`) | Verification Section (`verification.md`) | Gate 2 Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REQ-034` | `AC-034-1` | `ADR-025` | Section 1 (`REQ-034` / `AC-034-1`), Section 2.3 | `Task 1` | Run 2, Section 1 (`AC-034-1` Full-Depth Tree & `agy plugin validate` + Migration Docs) | `PASS` |
| `REQ-034` | `AC-034-2` | `ADR-025` | Section 1 (`REQ-034` / `AC-034-2`), Section 3 | `Task 1` | Run 2, Section 1 (`AC-034-2` Zero Forbidden `*.py`/`*.pyc`/`hooks.json`/`agents/*.md` Check) | `PASS` |
| `REQ-035` | `AC-035-1` | `ADR-025` | Section 1 (`REQ-035` / `AC-035-1`), Section 2.1, 2.2 | `Task 2` | Run 2, Section 2 (`AC-035-1` Gate 1 6-Row Table & Gate 2 8-Row Per-AC Matrix) | `PASS` |
| `REQ-035` | `AC-035-2` | `ADR-025` | Section 1 (`REQ-035` / `AC-035-2`), Section 3 | `Task 2` | Run 2, Section 2 (`AC-035-2` Gate Failure Reversion to `Planning` & Zero Gold-Plating Check) | `PASS` |
| `REQ-036` | `AC-036-1` | `ADR-025` | Section 1 (`REQ-036` / `AC-036-1`), Section 2.1, 2.2 | `Task 3` | Run 2, Section 3 (`AC-036-1` Counterpart Cascade Across 5 Prior Specs & 25 Historical ADR Blocks) | `PASS` |
| `REQ-036` | `AC-036-2` | `ADR-025` | Section 1 (`REQ-036` / `AC-036-2`), Section 3 | `Task 3` | Run 2, Section 3 (`AC-036-2` Disjoint Lineage Mode & Append-Only ADR Verification) | `PASS` |
| `REQ-037` | `AC-037-1` | `ADR-025` | Section 1 (`REQ-037` / `AC-037-1`), Section 2.1 | `Task 4` | Run 2, Section 4 (`AC-037-1` 6-State Lifecycle & Self-Contained Human `"Proceed"` Sign-Off) | `PASS` |
| `REQ-037` | `AC-037-2` | `ADR-025` | Section 1 (`REQ-037` / `AC-037-2`), Section 3 | `Task 4` | Run 1 & Run 2, Section 4 (`AC-037-2` Synchronized 3-Way Bug Decision Protocol & Live Triage) | `PASS` |

- **Zero Gold-Plating Check**: `PASS` — Every section in `design.md` and every task in `tasks.md` maps directly to `REQ-034` – `REQ-037` (`AC-034-1` – `AC-037-2`).
- **Zero Stale References Check**: `PASS` — All file paths in `design.md` and `tasks.md` match the repository structure on disk.
