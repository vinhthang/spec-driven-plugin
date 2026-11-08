# Five-document templates

Use these as starting structures, not as completed evidence. Replace angle-bracket fields with grounded content. Copy only applicable requirement/decision patterns. Allocate actual IDs using `SKILL.md`; the `001` examples assume an empty repository. Short documents are appropriate when the feature is simple.

## Catalog: `docs/specs/INDEX.md`

Create this after inspecting existing packages. Use one row per package; reserve its allocated IDs here. Keep status synchronized with the package's `spec.md`. Link related packages from their specifications.

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
- Type: <new feature / enhancement / fix / refactor>
- Status: Planning
- First entered In-Testing: Never
- Related specifications: None

## Problem and source intent

<Actual request or observed defect; distinguish quotations from paraphrases.>

## Repository grounding

<Inspected paths, symbols, current behavior, and constraints relevant to this feature.>

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

Append actual dated records to the final section: previous/new status, reason, and evidence link or the user's actual approval wording and covered scope. Preserve older entries. Set `First entered In-Testing` once using the actual date; never reset it when reopening a package. For an imported package, inspect history; if it is unknown, record `Unknown` and resolve it before choosing an in-place normative revision.

### Owner-deferred requirement pattern

Add `[PROVISIONAL]` to the heading, retain known intent/behavior, and add:

```markdown
- Open question: <One precise unresolved decision.>
- Owner deferral: <Actual owner instruction and date.>
- Blocked scope: <Acceptance criteria and tasks that depend on this answer.>
```

Do not invent acceptance criteria for the unknown answer. Reserve an AC ID for each unresolved outcome, describe what remains undecided, and mark its Gate 2 row and dependent tasks `BLOCKED`. When answered, record the resolution, finish the criteria, remove the provisional marker, and rerun the affected gates before execution.

### Delta requirement patterns

Use these in a new package when changing a requirement that has reached testing. Keep normal intent and lifecycle sections. Link to each prior requirement and preserve its body. See [lifecycle.md](lifecycle.md) for activation and history.

```markdown
### REQ-002: <Changed behavior>

- Changes: [<parent-feature>/REQ-001](../<parent-feature>/spec.md#req-001-title)
- Source intent: <Actual request, defect, or explicit derivation.>
- Previous contract: <Accurate prior observable behavior.>
- Statement: WHEN <event>, THE <system> SHALL <updated behavior>.
- AC-002-1 — Success: <Updated observable outcome.>
- AC-002-2 — Boundary/failure: <Updated observable outcome.>
```

```markdown
### REQ-003: <Retire a prior behavior>

- Retires: [<parent-feature>/REQ-001](../<parent-feature>/spec.md#req-001-title)
- Source intent: <Actual request, defect, or explicit derivation.>
- Previous contract: <Behavior being retired.>
- Retirement and migration rationale: <Why and how affected users/callers transition.>
- Statement: WHEN <retirement condition>, THE <system> SHALL <observable retirement or replacement behavior>.
- AC-003-1 — Success: <Old behavior removed/replaced and intended migration succeeds.>
- AC-003-2 — Boundary/failure: <Defined outcome for an old caller, retained data, or other relevant boundary.>
```

Resolve the sample anchors to actual headings. A retirement is work to verify and receives the same traceability as other requirements. New behavior in a delta uses the ordinary requirement pattern; no historical tags are needed for a fresh specification.

When a delta package reaches `In-Testing`, annotate the affected requirement in the parent `spec.md` without altering its original statement or acceptance-criterion bodies:

```markdown
- Current contract: Replaced by [<delta-feature>/REQ-002](../<delta-feature>/spec.md#req-002-changed-behavior)
```

## `decisions.md`

```markdown
# Decisions: <Feature title>

Governing specification: [spec.md](./spec.md)

## Architectural rationale

<Explain the consequential choices below, or why existing constraints leave no new architectural decision.>

## ADR-001: <Decision title>

- Governs: REQ-001
- State: Proposed
- Context and constraints: <Grounded facts.>
- Viable options: <Actual alternatives, or why the approach is constrained.>
- Decision: <Chosen approach and justification.>
- Costs and risks: <Concrete consequences and mitigations.>
- Rejected alternatives: <Reasons, or N/A with the constraint explanation.>
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

Omit the ADR block when no new decision is warranted, retain the rationale and Gate 1, and use explained `N/A` in Gate 2. A proposed decision can be evaluated before approval; record `Accepted` only when its scope is approved. Preserve accepted decision bodies; append a new ADR for a changed choice and annotate the old entry with a replacement link. Updating its state or adding that annotation is permitted.

## `design.md`

```markdown
# Design: <Feature title>

Sources: [spec.md](./spec.md), [decisions.md](./decisions.md)

## Components

| Requirement / AC | Path and symbol | Responsibility / change |
| --- | --- | --- |
| REQ-001 / AC-001-1, AC-001-2 | <actual path and symbol> | <concrete change> |

## Interfaces and flow

<Inputs, outputs, data structures, control flow, and relevant invariants.>

## Boundaries and recovery

<Handling for each failure/boundary criterion, including relevant compatibility constraints.>

## Dependencies and unresolved design work

None.
```

## `tasks.md`

```markdown
# Tasks: <Feature title>

Sources: [spec.md](./spec.md), [design.md](./design.md)

## Task 1: <Concrete deliverable>

- [ ] Complete the work and its applicable checks.
- Covers: REQ-001 / AC-001-1, AC-001-2
- Dependencies: None
- Blocked by: None
- Work: <Actionable change and meaningful validation; reproducer first for a bug when feasible.>
- Completion evidence: Not executed.

## Gate 2: traceability and readiness

| Requirement | AC | ADR or rationale | Design | Task | Planned verification | Status / reason |
| --- | --- | --- | --- | --- | --- | --- |
| REQ-001 | AC-001-1 | <ADR-001 or explained N/A> | [Interfaces](./design.md#interfaces-and-flow) | [Task 1](#task-1-concrete-deliverable) | [AC-001-1](./verification.md#ac-001-1) | UNCHECKED |
| REQ-001 | AC-001-2 | <ADR-001 or explained N/A> | [Boundaries](./design.md#boundaries-and-recovery) | [Task 1](#task-1-concrete-deliverable) | [AC-001-2](./verification.md#ac-001-2) | UNCHECKED |

- Backward scope check: UNCHECKED
- Reference and catalog consistency: UNCHECKED
```

Update task anchors to the actual task titles. Use one row per acceptance criterion; multiple tasks may be listed in a row. A task can cover several criteria. A `PASS` row validates the plan, not the implementation. Record `BLOCKED` for owner-deferred behavior and dependent tasks. Record `FAIL` for other defects. A task is complete only when its work and applicable checks are actually complete.

## `verification.md`

````markdown
# Verification: <Feature title>

Governing specification: [spec.md](./spec.md)

## Planned checks

### AC-001-1

- Method: <Test, inspection, or manual procedure and relevant environment.>
- Expected outcome: <Observable criterion for success.>
- Execution: Not run.

### AC-001-2

- Method: <Boundary/failure stimulus and procedure.>
- Expected outcome: <Observable criterion for success.>
- Execution: Not run.

## Execution evidence

No checks have been executed.

## Real-world observations

No real-world confirmation has been recorded.
````

After executing a check, append an actual dated run and replace `Not run` with a link to it. Do not overwrite earlier failed runs. A run contains:

- Criteria checked, environment/revision context, and exact command or manual procedure.
- Actual exit code for commands; `N/A — manual inspection` for non-command checks.
- Actual relevant output/observations, explicitly marking excerpts or redactions. Never store credentials or sensitive raw output in the package.
- Outcome per criterion: `PASS`, `FAIL`, or `BLOCKED`, with explanation and remaining limitations.

Use fenced `text` blocks for command output. Logs support the result; they do not replace checking the expected behavior. Human confirmation belongs in the approval/lifecycle history with a link to the relevant real-world observations.
