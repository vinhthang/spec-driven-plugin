# Spec-Driven Development Governance & Invariants

<rule name="spec-driven">
<description>
Governs how to write, self-validate, evolve, and test feature specifications using the 5-Document Architecture (spec.md, decisions.md, design.md, tasks.md, verification.md). Pure Markdown guidance — zero Python hooks.
</description>

<constraints>
- **1. Normative Authority & Primary Agent Boundary**:
  - **Normative Source (`spec.md` > `decisions.md`)**: Defines *what* (`REQ-xxx`, `AC-xxx`, `Non-Goals`) and *why* (`ADR-xxx`).
  - **Derived Blueprint (`design.md` > `tasks.md` > `verification.md`)**: Never write or update `design.md`, `tasks.md`, or `verification.md` before `spec.md` and `decisions.md` pass **Gate 1**.
  - **Primary Agent Boundary**: The Primary Agent authors `.md` specification files and never modifies source code or the runtime environment directly; delegate all code, test, build, and runtime changes to subagents after human `"Proceed"`.
- **2. Five Spec-Writing Quality Invariants**:
  - **Codebase Grounding**: Read existing files/symbols before writing `spec.md`. Never invent phantom APIs or duplicate existing abstractions.
  - **Intent Attribution & Non-Goals**: Every `REQ-xxx` must cite its `Source Intent` — either a verbatim user prompt, an observed defect, or an explicit derivation from a governing standard/ADR (`Derived from ADR-xxx / <standard>`). Never fabricate a user quote; if a requirement has no attributable intent, flag it as an open question to the user instead of guessing. Every `spec.md` must declare explicit `## Non-Goals`.
  - **EARS & Falsifiable Acceptance Criteria**: Every `REQ-xxx` must use EARS syntax (`WHEN / IF / WHILE ... THE <system> SHALL ...`) paired with observable `AC-xxx` criteria covering both happy paths and error/boundary cases. No vague adjectives or unresolved deferral placeholders.
  - **Anti-Strawman ADR Debate**: Every `ADR-xxx` in `decisions.md` must compare $\ge 2$ viable technical options on blast radius, coupling, and maintenance cost. `decisions.md` is append-only (`Status: Superseded by ADR-yyy`, never overwritten in-place).
  - **Cross-Spec Lineage & Counterpart Cascade**:
    - Every `spec.md` header must declare `Type` (`new feature | enhancement | fix | refactor`), `Version`, and `Lineage` (`Extends / Modifies` and `Supersedes`, set to `None` when not applicable), while `docs/specs/INDEX.md` uses the 6-column catalog format (`Feature ID | Title | Status | REQ Range | Key Decisions | Spec Path`).
    - Specifications in `Planning` or `In-Progress` are amended in-place (via Case 3).
    - **Whole-Spec Supersession (`Supersedes: <spec-id>`)**: Retires the prior specification in full; all requirements in the new spec are tagged `[NEW]`. If the superseded spec remains on disk, its `INDEX.md` row, `spec.md` status, and `decisions.md` ADRs are marked `Superseded`.
    - **Living-Spec Modification (`Extends / Modifies: <spec-id>`)**: Keeps the prior `In-Testing` or `Verified` specification active, tags individual changed/retired requirements in the delta spec per-ID (`[MODIFIES REQ-xxx in <spec-id>]` with `Previous Contract`, or `[DEPRECATED REQ-xxx in <spec-id>]` with `Deprecation & Migration Reason`). The prior specification's requirement prose and `AC-xxx` bodies remain **100% immutable**; only a counterpart lineage tag (`Modified by <new-spec-id>` / `Deprecated by <new-spec-id>`) on the `REQ-xxx` heading in `<prior-spec>/spec.md` and `<prior-spec>`'s row in `INDEX.md` may be appended.
- **3. Two-Stage Self-Validation Gate (With Written Receipt Tables)**:
  - **Gate 1 (Before Writing Derived Files)**: Self-validate `spec.md` and `decisions.md` against all 6 checks (Codebase Grounding, Intent & Non-Goals, EARS & Falsifiable ACs, Zero Deferral Placeholders, Anti-Strawman ADR Debate, and Cross-Spec Lineage/Cascade) and record a completed `## Gate 1: Normative Source Self-Validation` table in `decisions.md` before authoring `design.md`, `tasks.md`, or `verification.md`.
  - **Gate 2 (Before Asking Human to "Proceed")**: Self-validate `design.md`, `tasks.md`, and `verification.md` against `spec.md` and `decisions.md` (1-to-1 per-AC mapping, zero gold-plating, zero stale paths) and record a completed `## Gate 2: Derived File Self-Validation & Traceability Matrix` table in `tasks.md` before asking the human user to `"Proceed"`.
  - If any Gate 1 or Gate 2 check fails or is omitted, the specification remains in (or reverts to) `Planning` and derived work / code execution is blocked.
- **4. Six-State Specification Lifecycle (`In-Testing` Is Not `Verified`)**:
  - `Planning` $\to$ `In-Progress` *(requires Gate 1 + Gate 2 `PASS` and explicit human `"Proceed"` recorded in `spec.md` `Sign-off`)* $\to$ **`In-Testing`** *(all `- [x]` tasks complete and automated test output recorded in `verification.md`; real-world dogfooding active)* $\to$ **`Verified`** *(only after real-world usage and explicit human sign-off recorded in `spec.md` `Sign-off`)*.
  - Discovering a bug in `In-Testing` or `Verified` transitions the spec to `In-Progress` (Case 1) or `Planning` (Case 2 / Case 3) until resolved and re-verified. Replaced specs are `Superseded`; cancelled specs are `Abandoned`.
  - Never mark a specification `Verified` immediately after unit tests pass without human sign-off.
- **5. 3-Way Bug Decision Protocol**:
  - **Case 1 — Implementation Bug** *(Spec & Design are right; Code/Test is wrong)*: Do NOT edit `spec.md` or `decisions.md` (mints 0 new `REQ` IDs). Set status to `In-Progress`, add an unchecked `- [ ]` reproducer task in `tasks.md` citing `REQ-xxx`, fix via TDD Red $\to$ Green, check off `- [x]`, append verification run to `verification.md`, and set status to `In-Testing`.
  - **Case 2 — Design / Architecture Flaw** *(Spec is right; `design.md` or `ADR-xxx` failed in practice)*: Stop coding (mints 0 new `REQ` IDs). Set status to `Planning`, mark the flawed ADR `Superseded by ADR-yyy` in `decisions.md`, append `ADR-yyy`, re-run Gate 1 (`decisions.md`), update `design.md` and `tasks.md`, re-run Gate 2 (`tasks.md`), and obtain human `"Proceed"` before coding (`In-Progress`).
  - **Case 3 — Specification Gap or Flawed Requirement** *(`spec.md` missed an edge case or had a wrong requirement — Mints/Modifies `REQ` IDs)*: Stop coding. Set status to `Planning`, amend `spec.md` in-place (updating or adding `REQ-xxx` IDs) or create a `[MODIFIES]` delta spec (which mints new delta `REQ-xxx` IDs), update `decisions.md` if needed, re-run Gate 1 (`decisions.md`), cascade updates to `design.md` and `tasks.md`, re-run Gate 2 (`tasks.md`), and obtain human `"Proceed"` before coding (`In-Progress`).
</constraints>

<instructions>
- When authoring, updating, reviewing, or triaging a feature specification in `docs/specs/`, consult skill `spec-driven`.
</instructions>
</rule>
