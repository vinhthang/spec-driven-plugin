# Execution Tasks: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- [x] **Task 1 (`REQ-034`, `AC-034-1`, `AC-034-2`)**:
  - Remove `hooks.json`, `scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, `agents/traceability-auditor.md`, `tests/*.py`, `docs/specs/SELF_REVIEW.md`, and all 5 superseded `docs/specs/2026-10-*` directories (including `traceability_audit.json`) from `spec-driven-plugin`.
  - Rename the rule and skill to `rules/AGENTS.md` (`<rule name="spec-driven">`) and `skills/spec-driven/SKILL.md` (`name: spec-driven`), and document the legacy CLI/hook migration in `README.md` and `docs/specs/INDEX.md`.
- [x] **Task 2 (`REQ-035`, `AC-035-1`, `AC-035-2`)**:
  - Author `rules/AGENTS.md` and `skills/spec-driven/SKILL.md` defining the Normative Source (`spec.md`, `decisions.md`) vs. Derived Blueprint (`design.md`, `tasks.md`, `verification.md`) hierarchy, honest `Source Intent` attribution (user quote or explicit ADR/standard derivation), plain `[PROVISIONAL]` owner-deferred gating vs. forbidden lazy placeholders (`TODO`/`TBD`), and written **Gate 1** (`decisions.md`) and per-AC **Gate 2** (`tasks.md`) self-validation tables.
- [x] **Task 3 (`REQ-036`, `AC-036-1`, `AC-036-2`)**:
  - Define `Type`, `Version`, and `Lineage` headers in `spec.md`, the 6-column `INDEX.md` catalog format, and disjoint **In-Place Amendment**, **Whole-Spec Supersession**, and **Living-Spec Modification** rules (preserving parent requirement prose and `AC-xxx` bodies 100% immutable while updating heading lineage annotations to point directly in 1 hop to `<latest-spec-id>/REQ-yyy`) in `rules/AGENTS.md` and `skills/spec-driven/SKILL.md`.
- [x] **Task 4 (`REQ-037`, `AC-037-1`, `AC-037-2`)**:
  - Synchronize the 6-state lifecycle (`Planning`, `In-Progress`, `In-Testing`, `Verified`, `Superseded`, `Abandoned`), self-contained human `"Proceed"` `Sign-off` recording, and the 3-Way Bug Decision Protocol (`Case 1: Implementation Bug`, `Case 2: Design/ADR Flaw`, `Case 3: Spec Gap/Flaw`) across `spec.md`, `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, and `README.md`.

---

## Gate 2: Derived File Self-Validation & Traceability Matrix (`design.md`, `tasks.md`, `verification.md`)

| Requirement ID | Acceptance Criteria | Governing ADR | Design Section (`design.md`) | Execution Task (`tasks.md`) | Verification Section (`verification.md`) | Gate 2 Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REQ-034` | `AC-034-1` | `ADR-025` | Section 1 (`REQ-034` / `AC-034-1`), Section 2.1–2.3 | `Task 1` | Run 3, Section 1 (`AC-034-1` Full-Depth Tree & `agy plugin validate` + Migration Docs) | `PASS` |
| `REQ-034` | `AC-034-2` | `ADR-025` | Section 1 (`REQ-034` / `AC-034-2`), Section 3 | `Task 1` | Run 3, Section 1 (`AC-034-2` Zero Forbidden `*.py`/`hooks.json`/`SELF_REVIEW.md`/`2026-10-*` Check) | `PASS` |
| `REQ-035` | `AC-035-1` | `ADR-025` | Section 1 (`REQ-035` / `AC-035-1`), Section 2.1, 2.2 | `Task 2` | Run 3, Section 2 (`AC-035-1` Gate 1 6-Row Table, Gate 2 8-Row Per-AC Matrix & Honest `Source Intent`) | `PASS` |
| `REQ-035` | `AC-035-2` | `ADR-025` | Section 1 (`REQ-035` / `AC-035-2`), Section 3 | `Task 2` | Run 3, Section 2 (`AC-035-2` Gate Failure Reversion to `Planning` & Zero Gold-Plating Check) | `PASS` |
| `REQ-036` | `AC-036-1` | `ADR-025` | Section 1 (`REQ-036` / `AC-036-1`), Section 2.1, 2.2 | `Task 3` | Run 3, Section 3 (`AC-036-1` Disjoint Lineage, `Type`/`Version` Headers & Frozen Parent Prose) | `PASS` |
| `REQ-036` | `AC-036-2` | `ADR-025` | Section 1 (`REQ-036` / `AC-036-2`), Section 3 | `Task 3` | Run 3, Section 3 (`AC-036-2` Disjoint Lineage Mode & Append-Only ADR Verification) | `PASS` |
| `REQ-037` | `AC-037-1` | `ADR-025` | Section 1 (`REQ-037` / `AC-037-1`), Section 2.1 | `Task 4` | Run 3, Section 4 (`AC-037-1` 6-State Lifecycle & Self-Contained Human `"Proceed"` Sign-Off) | `PASS` |
| `REQ-037` | `AC-037-2` | `ADR-025` | Section 1 (`REQ-037` / `AC-037-2`), Section 3 | `Task 4` | Run 1–3, Section 4 (`AC-037-2` Synchronized 3-Way Bug Decision Protocol & Dogfooding Refinements) | `PASS` |

- **Zero Gold-Plating Check**: `PASS` — Every section in `design.md` and every task in `tasks.md` maps directly to `REQ-034` – `REQ-037` (`AC-034-1` – `AC-037-2`).
- **Zero Stale References Check**: `PASS` — All file paths (`rules/AGENTS.md`, `skills/spec-driven/SKILL.md`) in `design.md` and `tasks.md` match the repository structure on disk.
