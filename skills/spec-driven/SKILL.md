---
name: spec-driven
description: Author, review, and maintain code-grounded feature specifications in docs/specs using five documents, acceptance-criteria traceability, and evidence-based lifecycle updates. Do not use for unit-test *.spec.* files or routine edits unless docs/specs work is requested or governs the change.
---

# Spec-driven

Turn user intent and repository evidence into an implementable, verifiable specification. Use five documents per feature; keep each proportionate to the risk. A completed template or a self-assigned `PASS` is not proof that a feature works.

## Start with the requested work

- **New specification:** Read [templates.md](references/templates.md) (and [example.md](references/example.md) to calibrate brevity), then follow `## Ground the package` and `## Author and validate`.
- **Change, delta, defect, or status update:** Read [lifecycle.md](references/lifecycle.md) first to choose the revision route from testing history—not just today's status—and read [templates.md](references/templates.md) when adding delta or verification sections.
- **Specification review:** Follow `## Review an existing package`, consulting [lifecycle.md](references/lifecycle.md) and [templates.md](references/templates.md) to check lifecycle and gate compliance.

Keep documents readable in one sitting: a 1-requirement change needs only ~15–30 lines per file, one-line design bullets, and no `ADR-NNN` block when existing constraints fix the approach. Never pad sections by repeating prose across files. Do not impose `docs/specs/` on unrelated edits, and respect the user's authorization scope (authoring authorization does not authorize implementation, and implementation authorization does not authorize publishing or deployment).

## Ground the package

1. Read the request, repository instructions, relevant code and tests, and related specifications. Record actual paths, interfaces, constraints, and observed behavior. In brownfield code, distinguish current baseline behavior from requested changes; never invent APIs or user quotations.
2. Inspect `docs/specs/INDEX.md` and existing packages. If the index is absent, inventory existing packages before creating it from [templates.md](references/templates.md). Do not mistake a missing index for an empty repository.
3. Use `docs/specs/<YYYY-MM-DD-feature-slug>/` for a new package. Allocate repository-wide `REQ-NNN` and `ADR-NNN` IDs (zero-padded to at least three digits: `REQ-001`..`REQ-999`, `REQ-1000`+, preserving established repository conventions) above the highest allocation across active, historical, and index-reserved specs. When parallel branches may allocate IDs, recheck `INDEX.md` against the target base branch before saving or merging; never reuse retired IDs. Use `AC-<requirement-number>-<ordinal>` (`AC-001-1`); cross-spec links include `<feature-id>/REQ-NNN` and a relative link.
4. Ask only for missing decisions that materially affect correctness or scope. Record ordinary, reversible assumptions explicitly. If the owner explicitly defers a decision, scope it as `[PROVISIONAL]`; never disguise an open question as settled behavior.

## Document responsibilities

| Document | Responsibility |
| --- | --- |
| `spec.md` | Intent, scope, requirements, acceptance criteria, lifecycle history, and approval records. Governs observable behavior. |
| `decisions.md` | Architectural rationale, multi-option `ADR-NNN` tradeoffs when applicable, and Gate 1. Cannot override requirements. |
| `design.md` | Concrete components, interfaces, data/control flow, and boundary handling derived from the normative documents. |
| `tasks.md` | Executable work and Gate 2 mapping every acceptance criterion to rationale/ADR, design, task, and planned check. |
| `verification.md` | Planned checks (`AC-NNN-M (REQ-NNN)`) followed by actual run evidence and real-world observations. Evidence can expose defects in any document. |

`docs/specs/INDEX.md` is the catalog; keep its status and ID ranges synchronized with `spec.md` and `decisions.md`. Do not duplicate mutable package status headers in the other documents. When sources conflict, resolve the intent or design conflict before continuing dependent work; do not silently rewrite requirements to fit the code.

## Author and validate

### 1. Write the normative documents

Write `spec.md` and `decisions.md` first.

- Include the problem, grounded repository facts, explicit `Non-goals`, and attributable `Source intent` per requirement: a verbatim user quote, an observed defect, or an explained derivation from a named decision or standard.
- Use observable EARS statements: `WHEN <event>, THE <system> SHALL <behavior>`; use `WHILE` for state-dependent behavior and `IF ... THEN` for boundaries/failures. Give each requirement both success and boundary/failure criteria (use inspectable artifact checks for documentation-only behavior; do not invent runtime failures).
- Add an `ADR-NNN` block only when choosing among at least two genuinely viable options, comparing costs and risks. When constraints leave only one viable approach, omit `ADR-NNN` and explain those constraints under `## Architectural rationale` with `- Governs: REQ-NNN`.
- Mark owner-deferred requirements `### REQ-NNN: <Title> [PROVISIONAL]` with `Open question`, `Owner deferral`, `Blocked scope`, and reserved `Deferred [PROVISIONAL]` AC IDs per [templates.md](references/templates.md). Unowned `TODO`/`TBD` text and vague behavior fail Gate 1.

### 2. Gate 1: normative review

Complete the Gate 1 table in `decisions.md` with concrete evidence, replacing `UNCHECKED` with `PASS` or `FAIL` (when `python3` is available, run `python3 <skill-dir>/scripts/validate_specs.py docs/specs/<feature-id> --stage gate1`). Fix any `FAIL` or `UNCHECKED` check before writing or updating `design.md`, `tasks.md`, or `verification.md`.

Owner-deferred `[PROVISIONAL]` items pass Gate 1's criteria and open-decision checks (`PASS`) only when settled criteria are observable and deferred AC IDs are explicitly reserved and scoped; this permits design derivation, not coding of deferred behavior.

### 3. Derive design, tasks, and verification plans

After Gate 1 passes, write `design.md`, `tasks.md`, and `verification.md` using [templates.md](references/templates.md). Map actual paths/symbols, boundary handling, and task dependencies. Map every task to at least one requirement; reproduce bugs first when feasible.

Write `## Planned checks` (`### AC-001-1 (REQ-001)` with `Execution: Not run.`) before execution. Leave `## Execution evidence` and `## Real-world observations` unpopulated until checks actually run; a plan must never claim a test ran.

### 4. Gate 2: coverage and readiness

In `tasks.md`, give every acceptance criterion a row linking to its requirement, `ADR-NNN` (or `[Rationale](./decisions.md#architectural-rationale)` when constrained), design section, task, and planned verification anchor. Verify backward scope (every component and task serves a requirement) and reference/catalog consistency.

Rows start `UNCHECKED`; record `PASS`, `FAIL`, or `BLOCKED` with reasons (`PASS` validates the plan, not execution). Owner-deferred criteria and dependent tasks stay `BLOCKED`. When `python3` is available, run `python3 <skill-dir>/scripts/validate_specs.py docs/specs/<feature-id>` to verify links, anchors, IDs, and gate states deterministically; otherwise check them manually. Any `FAIL` or `UNCHECKED` row blocks implementation; independent settled work may proceed when all non-blocked rows pass and the owner authorizes that scope.

### 5. Execute only within authorization; record reality

Present the package and any `[PROVISIONAL]` boundaries. Record explicit human authorization and covered scope in ordinary language (no magic word required; reuse existing authorization when it clearly covers the package and scope).

Keep tasks and `verification.md` current during authorized execution, appending dated runs without overwriting earlier failed runs. Revalidate affected gates when normative or derived plans change. Follow [lifecycle.md](references/lifecycle.md) for defects, `[PROVISIONAL]` descoping, delta chains, and transitions: passing tasks and checks with zero `BLOCKED` criteria permits `In-Testing`; `Verified` additionally requires real usage and explicit human confirmation.

## Review an existing package

Keep reviews read-only: do not modify package files or write review files inside `docs/specs/` unless the user asks. Read [lifecycle.md](references/lifecycle.md) and [templates.md](references/templates.md) (and run `python3 <skill-dir>/scripts/validate_specs.py docs/specs/<feature-id>` when `python3` is available), then audit:

1. **Codebase grounding and drift:** Verify cited paths, interfaces, and live code against `spec.md` and `design.md`, flagging phantom APIs or out-of-band code drift.
2. **Normative rigor and Gate 1 honesty:** Check attributable intent, explicit non-goals, falsifiable success/boundary ACs, genuine multi-option ADRs vs. constrained rationale, and whether Gate 1 `PASS` claims match reality.
3. **Traceability and Gate 2 readiness:** Confirm bidirectional `REQ`/`AC` coverage across `design.md`, `tasks.md`, and `verification.md`, valid `#heading-anchors`, zero gold-plated tasks, and strict separation of planned checks from actual run evidence.
4. **Lifecycle and lineage compliance:** Verify `First entered In-Testing` routing (zero in-place edits to frozen `REQ`/`AC` bodies), 1-hop `Current contract` links across deltas, and `INDEX.md` status/ID synchronization.

Report concrete findings ordered by severity (`P0`/`P1` blocking correctness, traceability, or lifecycle violations; `P2` advisory clarity improvements) with `file:line`, `REQ`/`AC` IDs, consequences, and minimal fixes, ending with an explicit readiness verdict.
