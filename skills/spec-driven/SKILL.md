---
name: spec-driven
description: Author, review, and maintain code-grounded feature specifications in docs/specs using five documents, acceptance-criteria traceability, and evidence-based lifecycle updates. Use for specification work or when the user requests a spec-driven implementation workflow.
---

# Spec-driven

Turn user intent and repository evidence into an implementable, verifiable specification. Use five documents per feature; keep each as short as its job permits. A completed template or a self-assigned PASS is not proof that a feature works.

## Start with the requested work

- For a new specification, read [templates.md](references/templates.md), then follow the authoring workflow below.
- For a change, defect, or status update, also read [lifecycle.md](references/lifecycle.md) before editing. Choose the revision route from lifecycle history, not just today's status.
- For a review, inspect the existing package and relevant code first. Report concrete contradictions, missing behavior, unsupported scope, and unverifiable criteria with locations and consequences. Do not rewrite or implement unless requested.

Use this skill for the requested specification work; do not impose it on unrelated edits. Respect the user's scope and existing authorization. Implementation authorization does not authorize publishing, deployment, or unrelated configuration changes. No particular editor, tool, or agent arrangement is required.

## Ground the package

1. Read the request, applicable repository instructions, relevant code and tests, and related specifications. Record the actual paths, interfaces, constraints, and observed behavior that matter. Distinguish observations from assumptions; do not invent APIs or user quotations.
2. Inspect `docs/specs/INDEX.md` and existing packages. If the index is absent, inventory existing packages before creating it from the template. Do not mistake a missing index for an empty repository.
3. Use `docs/specs/<YYYY-MM-DD-feature-slug>/` for a new package. Allocate repository-wide `REQ-NNN` and `ADR-NNN` IDs above the highest existing allocation, including IDs reserved in the index or retained historical documents. An empty repository starts at `REQ-001` and `ADR-001`. Use `AC-<requirement-number>-<ordinal>` for acceptance criteria; cross-spec references include the feature ID and a link. Recheck allocations before saving when other work is concurrent; never reuse retired IDs.
4. Ask only for missing decisions that materially affect correctness or scope. State ordinary, reversible assumptions explicitly. If the owner explicitly defers a decision, identify its question and affected requirements/tasks; never disguise it as a settled requirement.

## Document responsibilities

| Document | Responsibility |
| --- | --- |
| `spec.md` | Intent, scope, requirements, acceptance criteria, lifecycle history, and approval records. Governs observable behavior. |
| `decisions.md` | Architectural choices and their rationale, plus Gate 1. Cannot override requirements. |
| `design.md` | Concrete components, interfaces, data/control flow, and boundary handling derived from the normative documents. |
| `tasks.md` | Executable work and Gate 2 mapping every acceptance criterion to design, task, and verification method. |
| `verification.md` | Planned checks followed by actual results and real-world observations. Evidence can expose defects in any document. |

`docs/specs/INDEX.md` is the catalog; keep its status consistent with `spec.md`. Do not duplicate mutable package status headers in the other documents. When sources conflict, resolve the intent or design conflict before continuing dependent work; do not silently change requirements to fit the code.

## Author and validate

### 1. Write the normative documents

Write `spec.md` and `decisions.md` first.

- Include the problem, inspected repository facts, explicit non-goals, and attributable source intent for every requirement: an actual user quote, an observed defect, or an explained derivation from a named decision/standard.
- Use observable EARS statements: `WHEN <event>, THE <system> SHALL <behavior>`; use `WHILE` for state-dependent behavior and `IF ... THEN` for failure handling. Precision matters more than formulaic wording.
- Give each requirement success criteria and meaningful failure/boundary criteria. Describe observable outcomes, not merely which files will change. For documentation-only behavior, use inspectable artifact checks; do not invent runtime failures.
- Record decisions where there is a consequential choice. Compare genuinely viable alternatives and explain costs and risks. If constraints determine the approach, state that rationale instead of inventing a second option. Keep `decisions.md` even when no ADR is warranted, stating why.
- Mark owner-deferred requirements `[PROVISIONAL]`, recording the open question and owner deferral. Unowned TODO/TBD text and unexplained vague behavior are unresolved defects, not acceptable decisions.

### 2. Gate 1: normative review

Complete the Gate 1 table in `decisions.md` with evidence, not prefilled success labels. Check grounding, intent/scope, falsifiable behavior, unresolved decisions, architectural rationale, and reference/ID consistency.

Use `UNCHECKED`, `PASS`, or `FAIL`. Fix failures before writing or updating dependent design, tasks, or verification plans. Owner-deferred questions may pass the open-decision check only when explicitly scoped; this permits design exploration, not implementation of unresolved behavior. Assess known criteria normally and explicitly identify deferred criteria rather than claiming their behavior is settled.

### 3. Derive design, tasks, and verification plans

After Gate 1 passes, write the remaining documents using the templates. Map actual paths and interfaces, failure handling, and dependencies. Make tasks independently understandable and map every task to a requirement. Choose verification that can distinguish correct from incorrect behavior. Use a failing reproducer for bugs when feasible; use inspection or manual checks when they are the appropriate evidence.

Write planned verification methods, including proposed commands where useful, before execution. Keep execution-evidence fields (commands actually run, output, exit codes, and observed results) empty until actually obtained. A plan must never claim that a test has run.

### 4. Gate 2: coverage and readiness

In `tasks.md`, give every acceptance criterion a row pointing to its requirement, applicable ADR (or explained `N/A`), design section, task, and verification section. Check backwards too: every proposed component/task must serve a requirement. Check that references resolve and the catalog is current.

Rows start `UNCHECKED`; record `PASS`, `FAIL`, or `BLOCKED` with reasons. `PASS` means the plan is complete and traceable, not that execution passed. An owner-deferred criterion stays `BLOCKED`, along with dependent tasks. Failures or unchecked rows prevent implementation. Independent, fully specified work may proceed when all other rows pass and the owner authorizes that scope; blocked work must remain unstarted.

### 5. Execute only within authorization; record reality

Present the concrete package and unresolved boundaries. Record actual explicit approval in ordinary language; no magic word is required. Reuse prior authorization when it clearly covers this package and scope; do not manufacture an extra approval loop. New unresolved product decisions or material scope changes require resolution before dependent work.

Keep tasks and evidence current during authorized execution. Revalidate affected gates when normative or derived plans change; appending genuine run evidence or updating lifecycle metadata alone does not require reauthoring the plan. Use [lifecycle.md](references/lifecycle.md) for defects and transitions. Completion of tasks and successful checks permits `In-Testing`; `Verified` additionally requires real usage and explicit human confirmation.
