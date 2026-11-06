# Architecture & Design: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- **Governing Spec**: [spec.md](./spec.md)
- **Governing Decisions**: [decisions.md](./decisions.md) (`ADR-025`)

## 1. Component & Symbol Map (Blast Radius)

| Requirement | Acceptance Criteria | Repository Path | Section / Artifact | Change Summary |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-034` | `AC-034-1` | `plugin.json`, `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `README.md`, `docs/specs/INDEX.md` | Declarative Plugin Surface (`spec-driven`) & Legacy Migration Section | Provide specification governance solely via `plugin.json`, `rules/AGENTS.md` (`<rule name="spec-driven">`), and `skills/spec-driven/SKILL.md` (`name: spec-driven`), and document the `v1.x` $\to$ `v2.x` migration in `README.md` and `INDEX.md`. |
| `REQ-034` | `AC-034-2` | `hooks.json`, `scripts/*.py`, `tests/*.py`, `agents/traceability-auditor.md`, `docs/specs/SELF_REVIEW.md`, `docs/specs/2026-10-*` | Removed Executable, Hook & Obsolete Docs | Delete all Python scripts, unit tests, `hooks.json`, `agents/traceability-auditor.md`, `SELF_REVIEW.md`, and all 5 superseded `2026-10-*` directories (including `traceability_audit.json`). |
| `REQ-035` | `AC-035-1` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/{decisions.md,tasks.md}` | `Gate 1` & `Gate 2` Written Tables + Honest `Source Intent` & `[PROVISIONAL]` Rule | Require the 6-row `## Gate 1: Normative Source Self-Validation` table in `decisions.md`, the per-AC `## Gate 2: Derived File Self-Validation & Traceability Matrix` table in `tasks.md`, honest `Source Intent` attribution, and plain `[PROVISIONAL]` tagging for owner-deferred questions. |
| `REQ-035` | `AC-035-2` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md` | Gate Failure, Unowned Placeholders & `[PROVISIONAL]` Coding Guard | Keep new specs in `Planning` (and revert updated specs to `Planning`) whenever any Gate 1 or Gate 2 row fails or contains unowned `TODO`/`TBD` placeholders, and block `In-Progress` coding of any `[PROVISIONAL]` task until the owner resolves the question. |
| `REQ-036` | `AC-036-1` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `docs/specs/INDEX.md` | Disjoint Lineage Modes, `Type`/`Version` Headers, Frozen Parent Prose & 1-Hop Pointer | Define `Type`, `Version`, and `Lineage` headers in `spec.md`, 6-column `INDEX.md`, and disjoint In-Place Amendment, Whole-Spec Supersession, and Living-Spec Modification (keeping parent requirement prose and `AC-xxx` bodies 100% immutable while updating heading lineage tags to point directly in 1 hop to `<latest-spec-id>/REQ-yyy`). |
| `REQ-036` | `AC-036-2` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md` | Lineage Conflict, Parent Prose, Multi-Hop Pointer & Append-Only ADR Guard | Fail Gate 1 Check 6 if a spec mixes `Supersedes` and `[MODIFIES]` on the same target spec, uses range tags, edits parent requirement prose, leaves a multi-hop stale pointer, or overwrites an ADR `Decision` body in-place. |
| `REQ-037` | `AC-037-1` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/{spec.md,verification.md}` | Six-State Lifecycle & Self-Contained `Sign-off` | Enforce `Planning` $\to$ `In-Progress` $\to$ `In-Testing` $\to$ `Verified` (plus `Superseded` / `Abandoned`) with verbatim human `"Proceed"` approval recorded in `spec.md` (`Sign-off`) and `verification.md`. |
| `REQ-037` | `AC-037-2` | `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `README.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/verification.md` | Synchronized 3-Way Bug Decision Protocol | Synchronize Case 1 (`In-Progress` $\to$ `- [ ]` reproducer task $\to$ TDD fix $\to$ `In-Testing`, minting 0 new `REQ` IDs), Case 2 (`Planning` $\to$ supersede ADR $\to$ Gate 1 + Gate 2 $\to$ human `"Proceed"`, minting 0 new `REQ` IDs), and Case 3 (`Planning` $\to$ amend spec in-place or `[MODIFIES]` delta spec $\to$ Gate 1 + Gate 2 $\to$ human `"Proceed"`, minting/modifying `REQ` IDs). |

## 2. Data Structures, Interfaces & Control Flow

### 2.1 Always-On Rule (`rules/AGENTS.md`)
- Loaded automatically by Google Antigravity (`<rule name="spec-driven">`).
- Enforces the Normative Source (`spec.md`, `decisions.md`) vs. Derived Blueprint (`design.md`, `tasks.md`, `verification.md`) hierarchy, the 5 Spec-Writing Quality Invariants, written Gate 1 & per-AC Gate 2 tables, the 6-state lifecycle, and the synchronized 3-Way Bug Decision Protocol, and routes specification work to skill `spec-driven`.

### 2.2 Authoring Skill (`skills/spec-driven/SKILL.md`)
- Loaded on demand when authoring, updating, reviewing, or triaging specifications in `docs/specs/`.
- Provides copy-ready templates for `INDEX.md`, `spec.md` (with `Type`, `Version`, `Lineage`, and `Source Intent` attribution rules), `decisions.md` (including the 6-row Gate 1 table), `design.md`, `tasks.md` (including the per-AC Gate 2 traceability matrix), and `verification.md`.

### 2.3 Legacy Surface Migration (`README.md` & `docs/specs/INDEX.md`)
- Documents the mapping from retired `v1.x` Python commands (`spec_checker.py --init`, `spec_checker.py --verify-evidence`, `spec_checker.py --close`, `traceability_audit.json`, `hooks.json`) to the `v2.x` Markdown templates and written Gate 1 / Gate 2 tables.

## 3. Error Handling, Edge Cases & Precedence
- **Forbidden Executable, Hook or Obsolete Artifact (`AC-034-2`)**: Any `*.py`, `*.pyc`, `__pycache__/`, `hooks.json`, `agents/*.md`, `traceability_audit.json`, `SELF_REVIEW.md`, or `2026-10-*` directory in the repository blocks `In-Testing` and `Verified` until removed.
- **Failed or Missing Gate 1 / Gate 2 Table (`AC-035-2`)**: If any row in the Gate 1 table (`decisions.md`) or per-AC Gate 2 table (`tasks.md`) is missing, has an empty evidence cell, or is marked `FAIL`, the specification remains in (or reverts to) `Planning` and cannot transition to `In-Progress`.
- **Mixed Lineage Modes, Parent Prose Edits or ADR Overwrites (`AC-036-2`)**: Mixing `Supersedes` and `[MODIFIES]` for the same target spec, using range tags, editing parent requirement prose during Living-Spec Modification, or overwriting an ADR `Decision` body in-place fails Gate 1 Check 6.
- **Defect Regression Transitions (`AC-037-2`)**: Discovering a defect in `In-Testing` or `Verified` transitions the spec to `In-Progress` (Case 1) or `Planning` (Case 2 / Case 3) and routes strictly through the 3-Way Bug Decision Protocol without weakening `spec.md` or silently diverging in code.
