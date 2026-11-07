# Architectural Decisions: Zero-Python Spec Authoring Standard, Self-Validation & Bug Triage

- **Feature ID**: `2026-11-05-zero-python-spec-authoring-standard`
- **Status**: `Accepted`

## `ADR-025`: Pure-Markdown Spec Authoring Skill (`spec-driven`) & Written Two-Stage Self-Validation Over Python `PreToolUse` Hooks
- **Status**: `Accepted` (Supersedes and retires all 25 historical ADR records `ADR-001` – `ADR-024` across the 5 removed `2026-10-18` through `2026-10-30` Python-enforcement specifications)
- **Governs**: `REQ-034`, `REQ-035`, `REQ-036`, `REQ-037`
- **Context**:
  Prior versions of `spec-driven-plugin` (`REQ-001` – `REQ-033`, `ADR-001` – `ADR-024`) attempted to police specification compliance mechanically via `hooks.json`, `scripts/spec-gate.py`, `scripts/spec_checker.py`, `scripts/semantic_checker.py`, and `agents/traceability-auditor.md`. Architectural review and real-world dogfooding (`Spec Builder v1` review by Muse) revealed key requirements:
  1. **Zero-Python Markdown Skill (`spec-driven`)**: Mechanical `PreToolUse` file-tool matching could not safely intercept shell commands (`run_command`) without breaking normal builds and test runs, while regex token counting did not teach models how to author crisp EARS requirements, falsifiable acceptance criteria, or cross-spec lineage.
  2. **Written Gate 1 & Gate 2 Self-Validation Tables**: Separating Normative Source validation (**Gate 1** in `decisions.md`) from Derived Blueprint validation (**Gate 2** in `tasks.md`) prevents wasted work on `design.md` and `tasks.md` when `spec.md` has unresolved gaps.
  3. **Dogfooding Clarifications (`v2.1`)**: Real-world application on `Spec Builder v1` showed the need to:
     - Allow `Source Intent` to cite an explicit governing ADR/standard derivation (`Derived from ADR-xxx / <standard>`) when a requirement is structural so agents never fabricate user quotes.
     - Clarify that during Living-Spec Modification (`Extends / Modifies`), the parent spec's requirement prose and `AC-xxx` bodies remain 100% immutable (only heading lineage tags and `INDEX.md` are updated).
     - Standardize `Type` and `Version` in the `spec.md` header while keeping `INDEX.md` at 6 columns, and remove the 28 obsolete `2026-10-*` / `SELF_REVIEW.md` files from this repository.
- **Options Considered**:
  1. **Option A (Zero-Python Markdown Rule `rules/AGENTS.md` + Skill `skills/spec-driven/SKILL.md` with Written Gate 1 / Gate 2 Tables)**: Remove `hooks.json`, `scripts/*.py`, `tests/*.py`, `agents/traceability-auditor.md`, `SELF_REVIEW.md`, and the 5 superseded `2026-10-*` spec folders. Provide `rules/AGENTS.md` (`<rule name="spec-driven">`) and `skills/spec-driven/SKILL.md` requiring written **Gate 1** and per-AC **Gate 2** tables, honest `Source Intent` attribution, frozen parent requirement prose on Living-Spec Modification, a 6-state lifecycle (`Planning`, `In-Progress`, `In-Testing`, `Verified`, `Superseded`, `Abandoned`), and the 3-Way Bug Decision Protocol.
  2. **Option B (Hardened Python `PreToolUse` Hook & Shell AST Parser)**: Retain `scripts/spec-gate.py`, `scripts/spec_checker.py`, and `scripts/semantic_checker.py`, and keep all 5 superseded `2026-10-*` spec directories in the working tree.
- **Decision**: Choose **Option A** because it eliminates hook lockouts and obsolete repository clutter, names the skill `spec-driven` to match the plugin, makes Gate 1 and Gate 2 directly inspectable as written Markdown tables inside the specification package, and resolves the 3 edge cases surfaced during real-world dogfooding.
- **Trade-offs & Risks**:
  - *Trade-off*: Removing `hooks.json` means the plugin no longer blocks tool calls at the OS process level.
  - *Mitigation*: Every specification package must include a written **Gate 1 Self-Validation Table** in `decisions.md`, a written per-AC **Gate 2 Traceability Matrix** in `tasks.md`, and a self-contained human `"Proceed"` `Sign-off` record in `spec.md` before transitioning out of `Planning` or into `Verified`.
- **Rejected Alternatives**: **Option B** was rejected because intercepting arbitrary shell commands in a `PreToolUse` hook is brittle, violates the user's explicit zero-Python requirement, and leaves 28 obsolete `v1.x` files cluttering the repository.
- **Blast Radius**:
  - `plugin.json`
  - `rules/AGENTS.md` (renamed from `rules/spec-standard.md`)
  - `skills/spec-driven/SKILL.md` (renamed from `skills/spec-standard/SKILL.md`)
  - `README.md`
  - `docs/specs/INDEX.md` and `docs/specs/2026-11-05-zero-python-spec-authoring-standard/`
  - Removed: `hooks.json`, `scripts/*.py`, `tests/*.py`, `agents/traceability-auditor.md`, `docs/specs/SELF_REVIEW.md`, `docs/specs/2026-10-*`

---

## Gate 1: Normative Source Self-Validation (`spec.md` & `decisions.md`)

| Gate 1 Check | Status | Verification Evidence |
| :--- | :--- | :--- |
| **1. Codebase Grounding** | `PASS` | Grounded in the full repository file tree (`find . -not -path '*/.git*' | sort`) confirming only `plugin.json`, `README.md`, `rules/AGENTS.md`, `skills/spec-driven/SKILL.md`, `docs/specs/INDEX.md`, and `docs/specs/2026-11-05-zero-python-spec-authoring-standard/` exist. |
| **2. User Intent & Non-Goals** | `PASS` | Section 1.2 quotes the user's 5 verbatim prompts; `REQ-034` – `REQ-037` each cite the exact verbatim prompt; Section 2 defines explicit `Non-Goals`. |
| **3. EARS & Falsifiable ACs** | `PASS` | Every requirement (`REQ-034`, `REQ-035`, `REQ-036`, `REQ-037`) uses explicit `WHEN ... THE ... SHALL` EARS syntax and pairs a Happy-Path criterion (`AC-034-1`, `AC-035-1`, `AC-036-1`, `AC-037-1`) with an explicit Error/Boundary criterion (`AC-034-2`, `AC-035-2`, `AC-036-2`, `AC-037-2`). |
| **4. Zero Deferral Placeholders** | `PASS` | Verified zero unowned deferral placeholders (`TODO`/`TBD`/`FIXME`) anywhere in `docs/specs/2026-11-05-zero-python-spec-authoring-standard/`, and documented the `[PROVISIONAL]` rule for owner-deferred questions. |
| **5. Anti-Strawman ADR Debate** | `PASS` | `ADR-025` evaluates two realistic options (`Option A: Zero-Python Markdown Rule + spec-driven Skill` vs. `Option B: Hardened Python Hook & Legacy Tree Retention`), documents `Trade-offs & Risks`, and explains `Rejected Alternatives`. |
| **6. Cross-Spec Lineage & Cascade** | `PASS` | `spec.md` declares `Type: refactor`, `Version: 2.3.0`, and `Lineage` (`Extends / Modifies: None`, `Supersedes: 2026-10-18 through 2026-10-30`), tags `REQ-034` – `REQ-037` as `[NEW]`, defines the 1-hop `Modified by <latest-spec-id>/REQ-yyy` cascade rule, and syncs `docs/specs/INDEX.md` to the clean 6-column catalog. |
