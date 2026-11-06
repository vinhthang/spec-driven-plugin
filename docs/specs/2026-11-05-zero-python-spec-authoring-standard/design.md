# Architecture & Design: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- **Governing Spec**: [spec.md](./spec.md)
- **Governing Decisions**: [decisions.md](./decisions.md) (`ADR-025`)

## 1. Component & Symbol Map (Blast Radius)

| Requirement | Acceptance Criteria | Repository Path | Section / Artifact | Change Summary |
| :--- | :--- | :--- | :--- | :--- |
| `REQ-034` | `AC-034-1` | `plugin.json`, `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `README.md`, `docs/specs/INDEX.md` | Declarative Plugin Surface & Legacy Migration Section | Provide specification governance solely via `plugin.json`, `rules/spec-standard.md`, and `skills/spec-standard/SKILL.md`, and document the `v1.x` $\to$ `v2.0` CLI/hook retirement migration in `README.md` and `INDEX.md`. |
| `REQ-034` | `AC-034-2` | `hooks.json`, `scripts/*.py`, `tests/*.py`, `agents/traceability-auditor.md` | Removed Executable & Hook Artifacts | Delete all Python scripts, unit tests, `__pycache__` / `.pyc` directories, `hooks.json`, and `agents/traceability-auditor.md` so zero forbidden artifacts exist in the repository. |
| `REQ-035` | `AC-035-1` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/{decisions.md,tasks.md}` | `Gate 1` & `Gate 2` Written Tables | Require the 6-row `## Gate 1: Normative Source Self-Validation` table in `decisions.md` and the per-AC `## Gate 2: Derived File Self-Validation & Traceability Matrix` table in `tasks.md`. |
| `REQ-035` | `AC-035-2` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md` | Gate Failure & Anti-Gold-Plating Enforcement | Keep new specs in `Planning` (and revert updated specs to `Planning`) whenever any Gate 1 or Gate 2 row is missing, empty, or `FAIL`, or when unmapped scope exists in `design.md` / `tasks.md`. |
| `REQ-036` | `AC-036-1` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `docs/specs/INDEX.md`, `docs/specs/2026-10-*/{spec.md,decisions.md}` | Disjoint Lineage Modes & Counterpart Cascade | Define In-Place Amendment, Whole-Spec Supersession (`Supersedes` + `[NEW]`), and Living-Spec Modification (`Extends / Modifies` + per-ID tags + counterpart annotations), and cascade `Superseded` across all 5 prior specs (`REQ-001` – `REQ-033` and all 25 historical ADR blocks `ADR-001` – `ADR-024`). |
| `REQ-036` | `AC-036-2` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md` | Lineage Conflict & Append-Only ADR Guard | Fail Gate 1 Check 6 if a spec mixes `Supersedes` and `[MODIFIES]` on the same target spec, uses range tags, overwrites an ADR `Decision` body in-place, or omits counterpart cascading. |
| `REQ-037` | `AC-037-1` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/{spec.md,verification.md}` | Six-State Lifecycle & Self-Contained `Sign-off` | Enforce `Planning` $\to$ `In-Progress` $\to$ `In-Testing` $\to$ `Verified` (plus `Superseded` / `Abandoned`) with verbatim human `"Proceed"` approval recorded in `spec.md` (`Sign-off`) and `verification.md`. |
| `REQ-037` | `AC-037-2` | `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `README.md`, `docs/specs/2026-11-05-zero-python-spec-authoring-standard/verification.md` | Synchronized 3-Way Bug Decision Protocol | Synchronize Case 1 (`In-Progress` $\to$ `- [ ]` reproducer task $\to$ TDD fix $\to$ `In-Testing`), Case 2 (`Planning` $\to$ supersede ADR $\to$ Gate 1 + Gate 2 $\to$ human `"Proceed"`), and Case 3 (`Planning` $\to$ amend spec / delta spec $\to$ Gate 1 + Gate 2 $\to$ human `"Proceed"`). |

## 2. Data Structures, Interfaces & Control Flow

### 2.1 Always-On Rule (`rules/spec-standard.md`)
- Loaded automatically by Google Antigravity via `plugin.json`.
- Enforces the Normative Source (`spec.md`, `decisions.md`) vs. Derived Blueprint (`design.md`, `tasks.md`, `verification.md`) hierarchy, the 5 Spec-Writing Quality Invariants, written Gate 1 & per-AC Gate 2 tables, the 6-state lifecycle, and the synchronized 3-Way Bug Decision Protocol.

### 2.2 Authoring Skill (`skills/spec-standard/SKILL.md`)
- Loaded on demand when authoring, updating, reviewing, or triaging specifications in `docs/specs/`.
- Provides copy-ready templates for `INDEX.md`, `spec.md`, `decisions.md` (including the 6-row Gate 1 table), `design.md`, `tasks.md` (including the per-AC Gate 2 traceability matrix), and `verification.md`.

### 2.3 Legacy Surface Migration (`README.md` & `docs/specs/INDEX.md`)
- Documents the mapping from retired `v1.x` Python commands (`spec_checker.py --init`, `spec_checker.py --verify-evidence`, `spec_checker.py --close`, `traceability_audit.json`, `hooks.json`) to the `v2.0` Markdown templates and written Gate 1 / Gate 2 tables.

## 3. Error Handling, Edge Cases & Precedence
- **Forbidden Executable or Hook Artifact (`AC-034-2`)**: Any `*.py`, `*.pyc`, `__pycache__/`, `hooks.json`, or `agents/*.md` file in the repository blocks `In-Testing` and `Verified` until removed.
- **Failed or Missing Gate 1 / Gate 2 Table (`AC-035-2`)**: If any row in the Gate 1 table (`decisions.md`) or per-AC Gate 2 table (`tasks.md`) is missing, has an empty evidence cell, or is marked `FAIL`, the specification remains in (or reverts to) `Planning` and cannot transition to `In-Progress`.
- **Mixed Lineage Modes or Missing Counterpart Cascade (`AC-036-2`)**: Mixing `Supersedes` and `[MODIFIES]` for the same target spec, using range tags, overwriting an ADR `Decision` body in-place, or omitting counterpart updates in `INDEX.md`, `<prior-spec>/spec.md`, or `<prior-spec>/decisions.md` fails Gate 1 Check 6.
- **Defect Regression Transitions (`AC-037-2`)**: Discovering a defect in `In-Testing` or `Verified` transitions the spec to `In-Progress` (Case 1) or `Planning` (Case 2 / Case 3) and routes strictly through the 3-Way Bug Decision Protocol without weakening `spec.md` or silently diverging in code.
