# Spec-Driven Plugin (`spec-driven`)

Zero-Python, 100% Markdown specification authoring standard for Google Antigravity. Focuses on helping models write crisp, code-grounded, falsifiable specifications using the **5-Document Architecture**, **Two-Stage Self-Validation**, **Cross-Spec Delta Lineage**, **Real-World Testing (`In-Testing` vs. `Verified`)**, and the **3-Way Bug Decision Protocol**.

---

## Core Architecture: Normative Source vs. Derived Files

$$\underbrace{\text{spec.md} > \text{decisions.md}}_{\text{Normative Source}} \xrightarrow{\text{Gate 1 Self-Check}} \underbrace{\text{design.md} > \text{tasks.md}}_{\text{Derived Blueprint}} \xrightarrow{\text{Gate 2 Self-Check}} \text{Human "Proceed"} \longrightarrow \underbrace{\text{verification.md}}_{\text{Empirical Falsifier}}$$

1. **`spec.md` (Normative Requirements)**: Honest `Source Intent` attribution (user quote or ADR/standard derivation), explicit `## Non-Goals`, `Type` & `Version` headers, cross-spec lineage (`[NEW]`, `[MODIFIES REQ-xxx]`, `[DEPRECATED REQ-xxx]` with frozen parent requirement prose), and EARS requirements (`WHEN / IF / WHILE ... THE <system> SHALL ...`) paired with falsifiable `AC-xxx` criteria.
2. **`decisions.md` (Append-Only ADRs)**: Compares $\ge 2$ viable technical designs on blast radius, coupling, and complexity (no strawman alternatives). Replaced decisions are marked `Superseded by ADR-yyy`. Includes the written **Gate 1 Self-Validation Table**.
3. **`design.md` (Derived Code Blueprint)**: Exact files, symbols, interfaces, and error-handling flows derived from `spec.md` + `decisions.md`.
4. **`tasks.md` (Derived TDD Checklist)**: Red $\to$ Green $\to$ Refactor task items and the written per-AC **Gate 2 Traceability Matrix** mapped 1-to-1 to `REQ-xxx` and `AC-xxx`.
5. **`verification.md` (Empirical Falsifier)**: Verbatim test and CLI output mapped to `REQ-xxx` and `AC-xxx`.

---

## Key Governance Pillars

- **Two-Stage Self-Validation**:
  - **Gate 1 (Before Writing Derived Files)**: Self-validate `spec.md` and `decisions.md` and record the 6-row Gate 1 table in `decisions.md` before generating `design.md` or `tasks.md`.
  - **Gate 2 (Before Asking Human to "Proceed")**: Verify 1-to-1 per-AC forward and backward traceability across `design.md`, `tasks.md`, and `verification.md` (zero gold-plating).
- **Post-Implementation Dogfooding Lifecycle**:
  - `Planning` $\to$ `In-Progress` $\to$ **`In-Testing`** *(Dogfooding after agent finishes code & unit tests)* $\to$ **`Verified`** *(only after real-world usage and human sign-off)*.
- **3-Way Bug Decision Protocol**:
  1. **Implementation Bug** *(Spec & Design right, Code wrong — Mints 0 new `REQ` IDs)*: Leave `spec.md` and `decisions.md` unchanged; add a reproducer task in `tasks.md` and fix via TDD Red $\to$ Green.
  2. **Design / Architecture Flaw** *(Spec right, `design.md` / `ADR-xxx` failed in practice — Mints 0 new `REQ` IDs)*: Stop coding; mark the broken ADR `Superseded by ADR-yyy` in `decisions.md`, re-run Gate 1, update `design.md` & `tasks.md`, re-run Gate 2, and get human **"Proceed"**.
  3. **Specification Gap or Wrong Requirement** *(`spec.md` missed an edge case or had a bad requirement — Mints/Modifies `REQ` IDs)*: Stop coding; amend `spec.md` in-place (updating/adding `REQ-xxx` IDs) or create a `[MODIFIES]` delta spec (which mints new delta `REQ-xxx` IDs), cascade `decisions.md` $\to$ `design.md` $\to$ `tasks.md`, run Gate 1 + Gate 2 self-checks, and get human **"Proceed"**.

---

## Bundled Files
- [`plugin.json`](plugin.json): Plugin manifest.
- [`rules/AGENTS.md`](rules/AGENTS.md): Concise always-on governance rule (`spec-driven`) and skill trigger.
- [`skills/spec-driven/SKILL.md`](skills/spec-driven/SKILL.md): Complete authoring playbook, EARS syntax guide, drop-in 5-Document templates, Gate 1 / Gate 2 self-validation checklists, and 3-way bug decision tree.

---

## Legacy CLI & Hook Migration (`v1.x` $\to$ `v2.0`)

All Python scripts, hooks, subagent manifests, and superseded `v1.x` specification folders (`REQ-001` – `REQ-033`, `2026-10-18` through `2026-10-30`) are **superseded and retired** by [`2026-11-05-zero-python-spec-authoring-standard`](docs/specs/2026-11-05-zero-python-spec-authoring-standard/spec.md):

| Retired `v1.x` Artifact / Command | `v2.0` Pure-Markdown Replacement |
| :--- | :--- |
| `scripts/spec_checker.py --init <feature-id>` | Scaffold `docs/specs/<feature-id>/{spec.md,decisions.md,design.md,tasks.md,verification.md}` using the copy-ready templates in `skills/spec-driven/SKILL.md`. |
| `scripts/spec_checker.py` & `scripts/semantic_checker.py` | Complete the written **Gate 1 Self-Validation Table** in `decisions.md` and the written **Gate 2 Traceability Matrix** in `tasks.md`. |
| `traceability_audit.json` & `agents/traceability-auditor.md` | Replaced by the inline **Gate 1** (`decisions.md`) and **Gate 2** (`tasks.md`) Markdown tables and explicit human `Sign-off` in `spec.md`. |
| `scripts/spec_checker.py --close <feature-id>` | Transition status in `INDEX.md` and `spec.md` to `In-Testing` upon completing `tasks.md` and `verification.md`, and to `Verified` after human sign-off. |
| `hooks.json` & `scripts/spec-gate.py` | Governed by `rules/AGENTS.md` and explicit human `"Proceed"` approval recorded in `spec.md`'s `Sign-off` header. |
