# Architectural Decisions: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- **Feature ID**: `2026-11-05-zero-python-spec-authoring-standard`
- **Status**: `Accepted`

## `ADR-025`: Pure-Markdown Spec Authoring Skill & Written Two-Stage Self-Validation Over Python `PreToolUse` Hooks
- **Status**: `Accepted` (Supersedes all 25 historical ADR records across the 5 prior specifications: `ADR-001` – `ADR-006` in [`2026-10-18-true-spec-driven-enforcement`](../2026-10-18-true-spec-driven-enforcement/decisions.md), `ADR-007` – `ADR-012` [`Tier-Aware Auditor Policy`] in [`2026-10-19-simplification-and-deduplication`](../2026-10-19-simplification-and-deduplication/decisions.md), `ADR-012` [`Normalize Volatile tasks.md Checkboxes`] – `ADR-014` in [`2026-10-19-sdd-lifecycle-and-ears-evolution`](../2026-10-19-sdd-lifecycle-and-ears-evolution/decisions.md), `ADR-015` – `ADR-019` in [`2026-10-20-harness2-artifact-gate-and-auditor-tools`](../2026-10-20-harness2-artifact-gate-and-auditor-tools/decisions.md), and `ADR-020` – `ADR-024` in [`2026-10-30-adversarial-adr-debate-and-spec-gate-hardening`](../2026-10-30-adversarial-adr-debate-and-spec-gate-hardening/decisions.md))
- **Governs**: `REQ-034`, `REQ-035`, `REQ-036`, `REQ-037`
- **Context**:
  Prior versions of `spec-driven-plugin` (`REQ-001` – `REQ-033`, `ADR-001` – `ADR-024`) attempted to police specification compliance mechanically via `hooks.json`, `scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, and `agents/traceability-auditor.md`. Architectural review and operational usage revealed four structural flaws:
  1. **Incomplete Hook Surface**: `PreToolUse` file-tool matching could not safely intercept shell commands (`run_command`) without breaking normal builds and test runs (`ADR-005`), leaving shell writes ungated while causing false-positive lockouts on legitimate edits (`ADR-010`, `ADR-014`).
  2. **Structural Regex vs. Spec Authoring Quality**: Checking for regex tokens (`REQ-\d+`, `ADR-\d+`) and SHA-256 file hashes (`traceability_audit.json`) verified token presence rather than teaching the model how to write clear EARS requirements, falsifiable acceptance criteria, cross-spec lineage deltas, or bug triage decisions.
  3. **Premature Terminal Closure**: Prior specs treated coding completion (`Implemented`) as terminal closure without a real-world dogfooding stage (`In-Testing`) or a structured decision tree when bugs were discovered during testing.
  4. **Direct Human Review**: The human user directly reviews specifications and explicitly approves execution in conversation (`"if a model make a bad spec, then I will not use it"`).
- **Options Considered**:
  1. **Option A (Zero-Python Markdown Rule + Skill with Written Gate 1 / Gate 2 Self-Validation Tables)**: Remove `hooks.json`, `scripts/*.py`, `tests/*.py`, and `agents/traceability-auditor.md`. Provide an always-on governance rule (`rules/spec-standard.md`) and comprehensive authoring skill (`skills/spec-standard/SKILL.md`) requiring written **Gate 1 (Normative Source)** and per-AC **Gate 2 (Derived Blueprint)** self-validation tables inside `decisions.md` and `tasks.md`, disjoint Whole-Spec Supersession vs. Living-Spec Modification lineage semantics with counterpart cascading, a 6-state lifecycle (`Planning`, `In-Progress`, `In-Testing`, `Verified`, `Superseded`, `Abandoned`), and the 3-Way Bug Decision Protocol.
  2. **Option B (Hardened Python `PreToolUse` Hook & Shell AST Parser)**: Retain `scripts/spec-gate.py`, `scripts/spec_checker.py`, and `scripts/semantic_checker.py`; add a shell command parser to block file mutations via `run_command`; and add CLI subcommands for `--in-testing` and bug triage.
- **Decision**: Choose **Option A (Zero-Python Markdown Rule + Skill with Written Gate 1 / Gate 2 Self-Validation Tables)** because it eliminates hook lockouts and maintenance overhead, makes Gate 1 and Gate 2 directly inspectable as written Markdown tables inside the specification package itself, and focuses the model's attention budget on authoring rigorous specifications for human review.
- **Trade-offs & Risks**:
  - *Trade-off*: Removing `hooks.json` means the plugin no longer blocks tool calls at the OS process level.
  - *Mitigation*: Every specification package must include a written **Gate 1 Self-Validation Table** in `decisions.md`, a written per-AC **Gate 2 Traceability Matrix** in `tasks.md`, and a self-contained human `"Proceed"` `Sign-off` record in `spec.md` before transitioning out of `Planning` or into `Verified`.
- **Rejected Alternatives**: **Option B** was rejected because intercepting arbitrary shell commands (`python3 -c`, `sed`, `tee`, `git apply`) in a `PreToolUse` hook is brittle and error-prone, violates the user's explicit zero-Python requirement, and does not improve the clarity of authored specifications.
- **Blast Radius**:
  - `plugin.json`
  - `rules/spec-standard.md`
  - `skills/spec-standard/SKILL.md`
  - `README.md`
  - `docs/specs/INDEX.md` and `docs/specs/2026-10-*` (counterpart cascade to `Superseded`)
  - Removed: `hooks.json`, `scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, `agents/traceability-auditor.md`, `tests/test_*.py`

---

## Gate 1: Normative Source Self-Validation (`spec.md` & `decisions.md`)

| Gate 1 Check | Status | Verification Evidence |
| :--- | :--- | :--- |
| **1. Codebase Grounding** | `PASS` | Grounded in the full repository file tree (`find /Users/thanghoang/github/spec-driven-plugin -not -path '*/.git*'`) confirming `plugin.json`, `rules/spec-standard.md`, `skills/spec-standard/SKILL.md`, `README.md`, and `docs/specs/**`, and verifying removal of `hooks.json`, `scripts/*.py`, `tests/*.py`, and `agents/traceability-auditor.md`. |
| **2. User Intent & Non-Goals** | `PASS` | Section 1.2 quotes the user's 4 verbatim prompts; `REQ-034` – `REQ-037` each cite the exact verbatim prompt; Section 2 defines explicit `Non-Goals` (no `PreToolUse` hooks, no unattended auto-approval, no source-file line-count caps). |
| **3. EARS & Falsifiable ACs** | `PASS` | Every requirement (`REQ-034`, `REQ-035`, `REQ-036`, `REQ-037`) uses explicit `WHEN ... THE ... SHALL` EARS syntax and pairs a Happy-Path criterion (`AC-034-1`, `AC-035-1`, `AC-036-1`, `AC-037-1`) with an explicit Error/Boundary criterion (`AC-034-2`, `AC-035-2`, `AC-036-2`, `AC-037-2`). |
| **4. Zero Deferral Placeholders** | `PASS` | Verified zero unresolved deferral placeholders anywhere in `docs/specs/2026-11-05-zero-python-spec-authoring-standard/`. |
| **5. Anti-Strawman ADR Debate** | `PASS` | `ADR-025` evaluates two realistic options (`Option A: Zero-Python Markdown Rule + Skill` vs. `Option B: Hardened Python Hook & Shell AST Parser`), documents `Trade-offs & Risks`, and explains `Rejected Alternatives`. |
| **6. Cross-Spec Lineage & Cascade** | `PASS` | `spec.md` declares Whole-Spec Supersession of all 5 prior Python-enforcement specs (`2026-10-18` through `2026-10-30`, `REQ-001` – `REQ-033`, and all 25 historical ADR blocks `ADR-001` – `ADR-024`, including both `2026-10-19` `ADR-012` records), tags `REQ-034` – `REQ-037` as `[NEW]`, and cascades `Superseded` into `docs/specs/INDEX.md` and all 5 counterpart `spec.md` and `decisions.md` files. |
