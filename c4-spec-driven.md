---
name: c4-spec-driven
description: Author, review, and maintain code-grounded feature specifications in docs/specs using five documents (spec.md, decisions.md, design.md, tasks.md, verification.md), acceptance-criteria traceability, Gate 1 and Gate 2 validation, and evidence-based lifecycle updates. Use when the user asks to write, update, review, or triage feature specs, ADRs, deltas, or docs/specs packages. Do not use for unit-test *.spec.* files or routine code edits unless docs/specs work is requested or governs the change.
---

# C4 Spec-Driven

Turn user intent and repository evidence into an implementable, verifiable specification in `docs/specs/<feature-id>/` using five proportionate documents and a shared `docs/specs/INDEX.md` catalog. A completed template or self-assigned `PASS` is not proof that a feature works.

## When to Use

- Writing a new feature specification grounded in repository code and user intent.
- Updating an existing `docs/specs/` package, authoring a linked delta, triaging a defect (Case 1, Case 2, or Case 3), or advancing lifecycle status.
- Auditing or reviewing an existing `docs/specs/<feature-id>/` package against live code, traceability, and lifecycle rules (read-only unless edits are requested).
- Implementing tasks governed by an approved `docs/specs/<feature-id>/` package while maintaining execution evidence.

## Scope, Brevity, and Authorization Rules

- Do not impose `docs/specs/` on routine edits or unit-test `*.spec.*` files unless requested or `docs/specs/` already governs the touched behavior.
- Respect authorization boundaries: requesting a specification or review does not authorize code changes, and implementation authorization does not authorize publishing or deployment.
- Follow the one-sitting rule: a 1-requirement change needs only ~15-30 lines per file, one-line design bullets, and no `ADR-NNN` block when existing constraints fix the approach. Never pad sections by repeating prose across files.
- **Gemini Web / Chat-Only Mode (no local filesystem, shell, or subagents):** When local file/shell tools are unavailable and target source files or `docs/specs/INDEX.md` are not attached in context, ask the user to upload or paste `INDEX.md` and target files first (or note that starting `REQ-NNN`/`ADR-NNN` numbering is provisional until `INDEX.md` is provided) rather than guessing paths or IDs. Emit all five package files plus the `docs/specs/INDEX.md` row as clearly labeled copy-ready markdown blocks (`#### File: docs/specs/<feature-id>/spec.md`, etc.), execute authorized tasks inline without subagent delegation, and keep `Status: In-Progress` (`Execution: Not run.`) until the user runs the commands locally and pastes real test output (unless an active sandbox can genuinely execute the self-contained check).

## Document Responsibilities

| Document | Responsibility |
| --- | --- |
| `docs/specs/INDEX.md` | Repository catalog tracking `Feature ID`, `Title`, `Status`, `REQ IDs`, `ADR IDs`, and spec links. Keep synchronized with `spec.md` and `decisions.md`. |
| `spec.md` | Intent, codebase grounding, non-goals, EARS requirements, acceptance criteria, `First entered In-Testing`, and approval/lifecycle history. |
| `decisions.md` | Architectural rationale, multi-option `ADR-NNN` tradeoffs (only when >=2 viable options exist), and Gate 1 normative review. Cannot override `spec.md`. |
| `design.md` | Concrete components, paths/symbols, interfaces, data/control flow, and boundary handling derived after Gate 1 passes. |
| `tasks.md` | Actionable work items with owned `- Files:` write-sets, dependencies, and Gate 2 bidirectional traceability table. |
| `verification.md` | Planned checks (`### AC-NNN-M (REQ-NNN)`) written before coding, followed by dated `### Run N — YYYY-MM-DD` execution logs and real-world observations. |

## Core Workflow

### 1. Ground the Package

1. Read the request, repository rules, relevant source/test files, and related specs (in chat-only mode without attached repo files, ask the user to upload or paste the target files first). Record real paths, symbols, constraints, and baseline behavior; never invent APIs or user quotes.
2. When local filesystem access is available, inspect `docs/specs/INDEX.md` and existing `docs/specs/*/` directories (if `INDEX.md` is missing on disk, inventory existing packages before creating it; do not mistake a missing index for an empty repo). In chat-only mode without `INDEX.md` attached, ask for `INDEX.md` or explicitly note that `REQ-NNN`/`ADR-NNN` IDs are provisional until verified against `INDEX.md`.
3. Name new packages `docs/specs/<YYYY-MM-DD-feature-slug>/`. Allocate repository-wide zero-padded `REQ-NNN` and `ADR-NNN` IDs (`REQ-001`..`REQ-999`, `REQ-1000`+) above the highest ID across active, historical, and index-reserved specs. Recheck `INDEX.md` against the base branch when parallel branches exist; never reuse retired IDs. Number acceptance criteria `AC-<req-num>-<ordinal>` (`AC-001-1`).
4. Ask only for missing decisions that materially change scope or correctness. Record reversible assumptions explicitly, and mark owner-deferred decisions `[PROVISIONAL]` rather than disguising open questions as settled behavior.

### 2. Author Normative Documents (`spec.md` and `decisions.md`)

1. Write `spec.md` and `decisions.md` before creating `design.md`, `tasks.md`, or `verification.md`.
2. Give every requirement attributable `Source intent` (verbatim user quote, observed defect, or derivation from a named decision/standard) and explicit `Non-goals`.
3. Write observable EARS statements (`WHEN <event>, THE <system> SHALL <behavior>`, `WHILE` for state, `IF ... THEN` for boundaries/failures) with both success and boundary/failure acceptance criteria.
4. Add `## ADR-NNN: <Title>` only when choosing among at least two genuinely viable options. When codebase constraints leave one viable path, omit `ADR-NNN` and record constraints under `## Architectural rationale` with `- Governs: REQ-NNN`.
5. For owner-deferred scope, use `### REQ-NNN: <Title> [PROVISIONAL]` with `Open question`, `Owner deferral`, `Blocked scope`, and reserved `Deferred [PROVISIONAL]` AC stubs. Unowned `TODO`/`TBD`/`FIXME` markers and leftover `<angle-bracket>` placeholders fail Gate 1.

### 3. Pass Gate 1 (Normative Review)

Complete all 6 checks in `decisions.md` (`## Gate 1: normative review`), replacing `UNCHECKED` with `PASS` or `FAIL` backed by concrete evidence. If `validate_specs.py` is available in the repo or plugin directory, run `python3 <path>/validate_specs.py docs/specs/<feature-id> --stage gate1`. Fix every `FAIL` or `UNCHECKED` row before deriving downstream files. Owner-deferred `[PROVISIONAL]` items pass Gate 1 only when settled criteria are observable and deferred AC IDs are explicitly reserved and scoped.

### 4. Derive `design.md`, `tasks.md`, and `verification.md`

1. Map concrete paths/symbols and boundary handling in `design.md`.
2. Partition `tasks.md` with explicit `- Files:`, `- Dependencies:`, and `- Covers:` fields per task. Tasks with `Dependencies: None` and strictly disjoint `- Files:` write-sets (including shared test files, `__init__.py`, and lockfiles) may run concurrently; overlapping `- Files:` must serialize via `- Dependencies:`. Map every task to at least one requirement and write failing reproducers first for bugs when feasible.
3. Populate `## Planned checks` in `verification.md` (`### AC-001-1 (REQ-001)` with `Execution: Not run.`). Leave `## Execution evidence` as `No checks have been executed.` and `## Real-world observations` as `No real-world confirmation has been recorded.` until checks actually run.

### 5. Pass Gate 2 (Traceability and Readiness)

1. In `tasks.md`, add one Gate 2 row per `AC` linking to `REQ-NNN`, `[ADR-NNN](./decisions.md#...)` (or `[Rationale](./decisions.md#architectural-rationale)`), design section, task anchor, and planned verification anchor, plus `- Backward scope check:` and `- Reference and catalog consistency:`.
2. Mark settled rows `PASS` (`PASS` validates plan readiness, not execution) and `[PROVISIONAL]` rows/tasks `BLOCKED`.
3. Run `python3 <path>/validate_specs.py docs/specs/<feature-id>` when available (or `--all` on `docs/specs`), or manually verify all links, GFM `#heading-anchors`, `INDEX.md` sync, ID uniqueness, and parallel `- Files:` disjointness. Any `FAIL` or `UNCHECKED` item blocks implementation.

### 6. Execute Within Authorization and Record Reality

1. Present the specification package and any `[PROVISIONAL]` / `BLOCKED` scope. Proceed to code changes only when explicit human authorization covers the scope.
2. Execute 1-2 coupled files—or all tasks in Gemini Web / chat-only sessions where subagents are unavailable—directly inline. Only when subagent tools exist and 3+ tasks have strictly disjoint `- Files:` write-sets may you delegate isolated parallel subagents and verify results before updating package docs.
3. When a local shell or active sandbox genuinely runs the checks, check off `- [x]` in `tasks.md` with `Completion evidence:` and append numbered `### Run N — YYYY-MM-DD` blocks in `verification.md` without overwriting prior failed runs. In Gemini Web / chat-only mode where repo checks cannot be executed directly, emit copy-ready markdown blocks (`#### File: docs/specs/<feature-id>/...`), keep `Status: In-Progress` and `Execution: Not run.`, and list the exact commands for the user to run locally and paste back.
4. Only after all tasks and planned checks pass with real execution output and zero `BLOCKED` or `[PROVISIONAL]` items, transition to `In-Testing` in both `spec.md` and `INDEX.md` and set `First entered In-Testing: YYYY-MM-DD` permanently. Never self-promote to `Verified` without recorded real-world usage observations and explicit human confirmation.

## Lifecycle, Revisions, and Defect Triage

### Six Lifecycle States

| State | Entry Condition |
| --- | --- |
| `Planning` | Authoring or revising normative requirements or architecture; decisions or gates incomplete. |
| `In-Progress` | Gate 1 and Gate 2 pass for authorized scope (only `[PROVISIONAL]` items `BLOCKED`) and implementation is authorized, or a Case 1 fix reopened the package. |
| `In-Testing` | All tasks `- [x]`, zero `BLOCKED` or `[PROVISIONAL]` items, and all planned checks pass with real execution evidence. Set `First entered In-Testing: YYYY-MM-DD` once and retain forever. |
| `Verified` | Real-world usage observations recorded in `verification.md` and explicit human confirmation logged in `spec.md`. |
| `Superseded` | A whole-package `Replaces` specification has reached at least `In-Testing`. |
| `Abandoned` | Unimplemented package or proposed delta explicitly cancelled by the owner. Never mark live `In-Testing`/`Verified` code `Abandoned`; use a retirement delta. |

### Revision Routing (`First entered In-Testing`)

Check `First entered In-Testing`, `## Approvals and lifecycle history`, and `verification.md` before editing normative text:

- **Never reached testing (`First entered In-Testing: Never`):** Amend `spec.md` in place. Keep `REQ-NNN` IDs for updated requirements, mint new repo-wide IDs for added requirements, reset affected Gate 1/2 rows to `UNCHECKED`, and return to `Planning`.
- **Reached testing (`First entered In-Testing: YYYY-MM-DD`):** Keep `REQ-NNN` statements and `AC-NNN-M` bodies byte-for-byte unchanged. Create a linked delta package in `Planning` with new repo-wide `REQ-NNN` IDs (`Proposed: Changes|Retires [<parent>](../<parent>/spec.md)`). When the delta reaches `In-Testing`, mark links `Implemented:` and insert `- Current contract: Changed by|Retired by [<delta>/REQ-MMM](../<delta>/spec.md#...)` immediately below the affected requirement heading on **every prior ancestor in the chain** (1-hop pointer).
- **Whole-package replacement:** Create a new package with `Proposed: Replaces [<prior>](../<prior>/spec.md)` covering all retained and changed behavior; transition the prior package to `Superseded` only when the replacement reaches `In-Testing`.

### Three Defect Cases

- **Case 1 (Implementation defect - requirements and design remain valid):** Keep `REQ`/`AC` and accepted `ADR` bodies unchanged (mint zero `REQ-NNN` IDs). Reopen to `In-Progress` in `spec.md` and `INDEX.md`, add an unchecked `- [ ]` reproducer/fix task, append a new `### Run N — YYYY-MM-DD` in `verification.md`, and return to `In-Testing` (keeping original `First entered In-Testing`).
- **Case 2 (Design or architecture defect - `REQ`/`AC` remain achievable):** Keep `REQ`/`AC` unchanged (mint zero `REQ-NNN` IDs). Return to `Planning` (keeping `First entered In-Testing`), append a new `ADR-NNN` (`State: Superseded by ADR-NNN` on the old ADR), reset affected Gate 1/2 rows to `UNCHECKED`, update derived docs, and re-verify. If an architectural failure on a tested package also forces changing `REQ`/`AC` (Case 2 + Case 3 coupled), record both the new `ADR-NNN` and changed `REQ-NNN` in a linked delta package instead of reopening the frozen parent.
- **Case 3 (Missing or changed requirement):** Check `First entered In-Testing` first; amend in place if `Never`, or create a linked delta package minting new `REQ-NNN` IDs if tested.
- **Descoping `[PROVISIONAL]` items / Out-of-band drift:** To ship settled work in a never-tested package before resolving a `[PROVISIONAL]` item, split the `[PROVISIONAL]` requirement (retaining its `REQ-NNN` ID) into a new `Planning` package or retire its ID into `Non-goals` without reuse, remove its `BLOCKED` rows/tasks, and re-validate Gates 1 and 2. For out-of-band code drift against an `In-Testing`/`Verified` spec, report exact `file:line` vs `REQ`/`AC` discrepancies to the owner and route as Case 1 or Case 3.

## Reviewing an Existing Package

Keep reviews read-only unless edits are requested. Audit four areas:

1. **Codebase grounding and drift:** Verify cited paths, symbols, and live code against `spec.md` and `design.md`.
2. **Normative rigor and Gate 1 honesty:** Check attributable intent, explicit non-goals, falsifiable success/boundary ACs, genuine multi-option ADRs vs constrained rationale, and truthful Gate 1 `PASS` evidence.
3. **Traceability and Gate 2 readiness:** Verify every `AC` maps across `decisions.md`, `design.md`, `tasks.md`, and `verification.md`, all `#heading-anchors` resolve, parallel tasks have disjoint `- Files:`, and planned checks are separated from actual runs.
4. **Lifecycle and lineage compliance:** Verify `First entered In-Testing` immutability, 1-hop `Current contract` delta links, and `INDEX.md` status/ID sync.

Report findings by severity (`P0`/`P1` blocking correctness, traceability, or lifecycle violations; `P2` clarity advisories) with `file:line`, `REQ`/`AC` IDs, minimal fixes, and an explicit readiness verdict.

## Five-Document Templates

Replace `<angle-bracket>` fields with grounded facts (leftover `<placeholders>` fail validation). Use `..` for inclusive ID ranges (`REQ-001..REQ-003`) and `,` for non-contiguous IDs (`REQ-001, REQ-003`) in `INDEX.md` - never spaced hyphens (`REQ-001 - REQ-003`).

### `docs/specs/INDEX.md`

```markdown
# Feature specifications

| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |
| --- | --- | --- | --- | --- | --- |
| 2026-11-18-feature-slug | Short title | Planning | REQ-001 | None | [spec](./2026-11-18-feature-slug/spec.md) |
```

### `spec.md` (with `[PROVISIONAL]` and Delta Patterns)

```markdown
# Feature title

- Feature ID: 2026-11-18-feature-slug
- Type: enhancement
- Status: Planning
- First entered In-Testing: Never
- Related specifications: None

## Problem and source intent

Actual user request or observed defect, distinguishing verbatim quotes from paraphrases.

## Repository grounding

Inspected paths, symbols, current baseline behavior, and constraints.

## Non-goals

- Explicit excluded scope.

## Requirements

### REQ-001: Requirement title

- Source intent: Verbatim quote, defect, or named ADR/standard derivation.
- Statement: WHEN event occurs, THE system SHALL perform observable behavior.
- AC-001-1 — Success: Deterministic observable outcome.
- AC-001-2 — Boundary/failure: IF boundary condition holds, THEN observable outcome occurs.

## Assumptions and owner-deferred questions

None.

## Approvals and lifecycle history

No approval or lifecycle transition has been recorded yet.
```

For `[PROVISIONAL]` requirements, keep `[PROVISIONAL]` at the end of `### REQ-NNN: Title [PROVISIONAL]`, add `- Open question:`, `- Owner deferral:`, `- Blocked scope:`, and `- AC-NNN-M — Deferred [PROVISIONAL]: ...`. For delta requirements on tested packages, add `- Changes: [parent/REQ-001](../parent/spec.md#req-001-title)` (or `- Retires:` plus `- Retirement and migration rationale:`) and `- Previous contract:` above `- Statement:`.

### `decisions.md`

```markdown
# Decisions: Feature title

Governing specification: [spec.md](./spec.md)

## Architectural rationale

- Governs: REQ-001

Explain why codebase constraints fix the approach, or introduce multi-option ADRs below.

## ADR-001: Decision title

- Governs: REQ-001
- State: Proposed
- Context and constraints: Grounded facts.
- Viable options: Option A vs Option B (omit ADR block if only one viable option exists).
- Decision: Chosen option and justification.
- Costs and risks: Concrete tradeoffs and mitigations.
- Rejected alternatives: Why viable alternatives were rejected.
- Affected components: Actual paths and interfaces.

## Gate 1: normative review

| Check | Status | Evidence / required correction |
| --- | --- | --- |
| Codebase grounding | UNCHECKED | |
| Attributable intent and explicit scope | UNCHECKED | |
| Observable requirements and meaningful acceptance criteria | UNCHECKED | |
| Assumptions and owner-deferred questions are explicit | UNCHECKED | |
| Architectural rationale respects requirements | UNCHECKED | |
| IDs, references, and revision route are consistent | UNCHECKED | |
```

### `design.md`

```markdown
# Design: Feature title

Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)

## Components

| Requirement / AC | Path and symbol | Responsibility / change |
| --- | --- | --- |
| REQ-001 / AC-001-1, AC-001-2 | `src/module.py::func` | Concrete change summary |

## Interfaces and flow

- Signatures, inputs/outputs, control flow, and invariants.

## Boundaries and recovery

- Handling for each boundary/failure AC and compatibility constraint.

## Dependencies and unresolved design work

None.
```

### `tasks.md`

```markdown
# Tasks: Feature title

Sources: [spec.md](./spec.md), [design.md](./design.md)

## Task 1: Concrete deliverable

- [ ] Complete the work and its applicable checks.
- Covers: REQ-001 / AC-001-1, AC-001-2
- Files: `src/module.py`, `tests/test_module.py`
- Dependencies: None
- Blocked by: None
- Work: Write failing tests first when feasible, then implement change.
- Completion evidence: Not executed.

## Gate 2: traceability and readiness

| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | AC-001-1 | [Rationale](./decisions.md#architectural-rationale) | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-concrete-deliverable) | [AC-001-1](./verification.md#ac-001-1-req-001) | UNCHECKED |
| REQ-001 | AC-001-2 | [Rationale](./decisions.md#architectural-rationale) | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-concrete-deliverable) | [AC-001-2](./verification.md#ac-001-2-req-001) | UNCHECKED |

- Backward scope check: UNCHECKED
- Reference and catalog consistency: UNCHECKED
```

### `verification.md`

````markdown
# Verification: Feature title

Governing specification: [spec.md](./spec.md)

## Planned checks

### AC-001-1 (REQ-001)

- Method: Automated test or inspection procedure and environment.
- Expected outcome: Deterministic pass condition.
- Execution: Not run.

### AC-001-2 (REQ-001)

- Method: Boundary/failure stimulus and procedure.
- Expected outcome: Deterministic boundary outcome.
- Execution: Not run.

## Execution evidence

No checks have been executed.

## Real-world observations

No real-world confirmation has been recorded.
````

When checks actually execute, replace `No checks have been executed.` with numbered runs (`### Run 1 — YYYY-MM-DD` with `- Checked:`, `- Command:`, `- Output excerpt:`, and `- Result: AC-001-1 PASS, AC-001-2 PASS — note`) and link `Execution: [Run 1](#run-1--yyyy-mm-dd)`.

## Gotchas

- Verify GFM heading slugs (`#ac-001-1-req-001`, `#run-1--2026-11-18` with a double hyphen from `### Run 1 — 2026-11-18`) and relative paths across all five files so zero broken anchors remain across Gemini, Antigravity, Codex, and `validate_specs.py`.
- Reference every package `REQ-NNN` token in `decisions.md`, `design.md`, `tasks.md`, and `verification.md` so cross-document coverage checks pass.
- Never fabricate test output or advance to `In-Testing` without real command execution; in chat-only environments without a test runner, keep `Status: In-Progress` and `Execution: Not run.` until the user supplies real run output.
