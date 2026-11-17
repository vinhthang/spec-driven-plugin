# Five-document templates

Use these as starting structures, not pre-approved evidence. Replace `<angle-bracket>` fields with grounded facts and delete unused patterns. Allocate repository-wide IDs per [SKILL.md](../SKILL.md); `001` assumes an empty repository. Keep files concise—see [example.md](example.md) for a complete, right-sized 1-requirement package.

## Catalog: `docs/specs/INDEX.md`

Create after inventorying any existing packages. Use one 6-column row per package; keep `Status`, `REQ IDs`, and `ADR IDs` synchronized with `spec.md` and `decisions.md`.

```markdown
# Feature specifications

| Feature ID | Title | Status | REQ IDs | ADR IDs | Specification |
| --- | --- | --- | --- | --- | --- |
| <feature-id> | <title> | Planning | REQ-001 | None | [spec](./<feature-id>/spec.md) |
```

## `spec.md`

```markdown
# <Feature title>

- Feature ID: <YYYY-MM-DD-feature-slug>
- Type: <new feature | enhancement | fix | refactor>
- Status: Planning
- First entered In-Testing: Never
- Related specifications: None

## Problem and source intent

<Actual request or observed defect; distinguish verbatim quotations from paraphrases.>

## Repository grounding

<Inspected paths, symbols, current baseline behavior, and constraints relevant to this feature.>

## Non-goals

- <Explicit excluded behavior or scope.>

## Requirements

### REQ-001: <Title>

- Source intent: <Actual quote, observed defect, or explained ADR/standard derivation.>
- Statement: WHEN <event>, THE <system> SHALL <observable behavior>.
- AC-001-1 — Success: <Deterministic observable outcome.>
- AC-001-2 — Boundary/failure: IF <relevant condition>, THEN <observable outcome>.

## Assumptions and owner-deferred questions

None.

## Approvals and lifecycle history

No approval or lifecycle transition has been recorded yet.
```

- **`Related specifications` values:** Use `None`, or label status and direction explicitly: `Proposed: Changes [<parent-id>](../<parent-id>/spec.md)`, `Implemented: Changes [<parent-id>](../<parent-id>/spec.md)`, `Proposed: Replaces [<prior-id>](../<prior-id>/spec.md)`, or `Replaced by [<new-id>](../<new-id>/spec.md)`.
- **`Assumptions and owner-deferred questions`:** Record ordinary reversible assumptions here, plus package-wide open questions or cross-links to `[PROVISIONAL]` requirements (`See REQ-001 [PROVISIONAL]`).
- **`Approvals and lifecycle history`:** Append dated entries recording `previous -> new status`, reason, and run link or the user's actual approval wording and covered scope. Set `First entered In-Testing` once (`YYYY-MM-DD`) upon first entry; never reset it. Use `Unknown` for imported packages with unclear testing history until clarified.

### Owner-deferred requirement pattern

Place `[PROVISIONAL]` at the **end** of the heading so heading structure stays uniform, record deferral metadata, and reserve AC IDs without inventing settled behavior:

```markdown
### REQ-001: <Title> [PROVISIONAL]

- Source intent: <Actual quote, observed defect, or explained derivation.>
- Open question: <One precise unresolved decision.>
- Owner deferral: <Actual owner instruction and date.>
- Blocked scope: <AC-001-2 and dependent tasks.>
- Statement: WHEN <known trigger>, THE <system> SHALL <settled portion; note deferred aspect>.
- AC-001-1 — Success: <Deterministic observable outcome for settled portion, if any.>
- AC-001-2 — Deferred [PROVISIONAL]: <Undecided outcome pending open question; blocked until owner resolves.>
```

Mark `AC-001-2`'s row in Gate 2 and dependent tasks `BLOCKED`, and add a matching stub in `verification.md` (`Execution: Blocked pending REQ-001 [PROVISIONAL] resolution.`) so Gate 2 links resolve. See [lifecycle.md](lifecycle.md) to resolve or descope `[PROVISIONAL]` items.

### Delta requirement patterns

Use in a linked delta package when changing or retiring behavior from a package that has reached testing (`First entered In-Testing` is set). Mint new repo-wide `REQ-NNN` IDs; new added behavior in a delta uses the standard `### REQ-NNN` pattern.

```markdown
### REQ-002: <Changed behavior>

- Changes: [<parent-feature>/REQ-001](../<parent-feature>/spec.md#req-001-title)
- Source intent: <Actual request, defect, or explicit derivation.>
- Previous contract: <Accurate prior observable behavior.>
- Statement: WHEN <event>, THE <system> SHALL <updated behavior>.
- AC-002-1 — Success: <Updated observable outcome.>
- AC-002-2 — Boundary/failure: IF <condition>, THEN <updated observable outcome>.
```

```markdown
### REQ-003: <Retire a prior behavior>

- Retires: [<parent-feature>/REQ-001](../<parent-feature>/spec.md#req-001-title)
- Source intent: <Actual request, defect, or explicit derivation.>
- Previous contract: <Behavior being retired.>
- Retirement and migration rationale: <Why and how affected callers/data transition.>
- Statement: WHEN <retirement condition>, THE <system> SHALL <observable retirement or migration outcome>.
- AC-003-1 — Success: <Old behavior removed/replaced and intended migration succeeds.>
- AC-003-2 — Boundary/failure: IF <legacy caller or retained data condition>, THEN <defined outcome>.
```

When the delta reaches `In-Testing`, insert a 1-hop `- Current contract:` line **immediately below** the affected heading in the parent `spec.md` (above `- Source intent:`), leaving the original statement and AC bullets byte-for-byte untouched:

```markdown
### REQ-001: <Title>

- Current contract: Changed by [<delta-feature>/REQ-002](../<delta-feature>/spec.md#req-002-changed-behavior)
- Source intent: <Original untouched text...>
```

For a retired requirement, use `Retired by`:

```markdown
- Current contract: Retired by [<delta-feature>/REQ-003](../<delta-feature>/spec.md#req-003-retire-a-prior-behavior)
```

## `decisions.md`

```markdown
# Decisions: <Feature title>

Governing specification: [spec.md](./spec.md)

## Architectural rationale

- Governs: REQ-001

<Explain the consequential choices below, or why existing codebase constraints leave only one viable approach.>

## ADR-001: <Decision title>

- Governs: REQ-001
- State: Proposed
- Context and constraints: <Grounded facts.>
- Viable options: <Option A vs. Option B (at least two genuinely viable options).>
- Decision: <Chosen option and justification.>
- Costs and risks: <Concrete consequences and mitigations.>
- Rejected alternatives: <Why non-selected viable options were rejected.>
- Affected components: <Actual paths/interfaces.>

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

Omit the `## ADR-001` block when existing constraints leave no genuine multi-option choice—retain `## Architectural rationale` (including `- Governs: REQ-001` so requirement traceability holds) and `## Gate 1`, and link `[Rationale](./decisions.md#architectural-rationale)` in Gate 2. ADR `State:` values are `Proposed`, `Accepted` (once scope is approved), `Superseded by ADR-NNN` (preserving the accepted body and appending `ADR-NNN`), or `Abandoned`.

## `design.md`

```markdown
# Design: <Feature title>

Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)

## Components

| Requirement / AC | Path and symbol | Responsibility / change |
| --- | --- | --- |
| REQ-001 / AC-001-1, AC-001-2 | <actual path and symbol> | <concrete change> |

## Interfaces and flow

<Inputs, outputs, data structures, control flow, and invariants.>

## Boundaries and recovery

<Handling for each boundary/failure criterion and compatibility constraint.>

## Dependencies and unresolved design work

None.
```

For small single-component changes, keep `Interfaces and flow` and `Boundaries and recovery` to one or two concise bullets without repeating `spec.md`.

## `tasks.md`

```markdown
# Tasks: <Feature title>

Sources: [spec.md](./spec.md), [design.md](./design.md)

## Task 1: <Concrete deliverable>

- [ ] Complete the work and its applicable checks.
- Covers: REQ-001 / AC-001-1, AC-001-2
- Dependencies: None
- Blocked by: None
- Work: <Actionable change and validation; failing reproducer first for bugs when feasible.>
- Completion evidence: Not executed.

## Gate 2: traceability and readiness

| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | AC-001-1 | <[ADR-001](./decisions.md#adr-001-decision-title) or [Rationale](./decisions.md#architectural-rationale)> | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-concrete-deliverable) | [AC-001-1](./verification.md#ac-001-1-req-001) | UNCHECKED |
| REQ-001 | AC-001-2 | <[ADR-001](./decisions.md#adr-001-decision-title) or [Rationale](./decisions.md#architectural-rationale)> | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-concrete-deliverable) | [AC-001-2](./verification.md#ac-001-2-req-001) | UNCHECKED |

- Backward scope check: UNCHECKED
- Reference and catalog consistency: UNCHECKED
```

Update heading anchors to match actual titles. Use one Gate 2 row per `AC`; a task may cover several criteria, and multiple tasks may appear in one row. `PASS` validates plan completeness, not code execution. Use `BLOCKED` for `[PROVISIONAL]` scope and `FAIL` for missing/broken coverage. Check off `- [x]` and fill `Completion evidence:` only after work and checks succeed.

## `verification.md`

````markdown
# Verification: <Feature title>

Governing specification: [spec.md](./spec.md)

## Planned checks

### AC-001-1 (REQ-001)

- Method: <Test, inspection, or manual procedure and environment.>
- Expected outcome: <Observable criterion for success.>
- Execution: Not run.

### AC-001-2 (REQ-001)

- Method: <Boundary/failure stimulus and procedure.>
- Expected outcome: <Observable criterion for success.>
- Execution: Not run.

## Execution evidence

No checks have been executed.

## Real-world observations

No real-world confirmation has been recorded.
````

Include `(REQ-NNN)` in each planned check heading so requirement coverage is explicit. For a `[PROVISIONAL]` criterion, record `Method: Blocked pending REQ-NNN [PROVISIONAL] resolution.` and `Execution: Blocked pending REQ-NNN [PROVISIONAL] resolution.` until resolved.

After running checks, replace `No checks have been executed.` with numbered runs (preserving any earlier failed runs) and update `Execution: Not run.` to `[Run 1](#run-1--yyyy-mm-dd)`:

````markdown
### Run 1 — <YYYY-MM-DD>

- Checked: REQ-001 / AC-001-1, AC-001-2 (`<git-rev-or-env>`)
- Command: `<exact command or N/A — manual inspection>` (exit code: `<0>`)
- Output excerpt:
  ```text
  <concise relevant output; redact secrets>
  ```
- Result: AC-001-1 `PASS`, AC-001-2 `PASS` — <1-line verification note and any remaining limitation>.
````

Human sign-off belongs in `spec.md` (`## Approvals and lifecycle history`) linking to `## Real-world observations`.
