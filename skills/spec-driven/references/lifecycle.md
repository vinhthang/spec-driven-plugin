# Lifecycle and revision guidance

Read this before changing an existing specification, triaging a defect, resolving or descoping `[PROVISIONAL]` items, or updating status. `spec.md` and `docs/specs/INDEX.md` must always agree on status and allocated IDs; `spec.md` records why transitions happened, and `verification.md` holds the supporting observations.

## States and evidence

| State | Entry condition |
| --- | --- |
| `Planning` | Authoring or revising governing requirements or architecture; required decisions or gates are incomplete. |
| `In-Progress` | Gate 1 and Gate 2 pass for the authorized scope (with only `[PROVISIONAL]` scope `BLOCKED`) and explicit implementation authorization is recorded; or an authorized Case 1 fix has reopened the package. |
| `In-Testing` | All tasks are complete (`- [x]`), zero `BLOCKED` or `[PROVISIONAL]` criteria remain, and all planned checks have passed with actual execution evidence. Real-world evaluation is pending or underway. |
| `Verified` | Real-world usage observations are recorded and the human explicitly confirms the feature works for the intended scope. Passing automated tests alone is insufficient. |
| `Superseded` | A whole-package replacement specification has reached at least `In-Testing`. A proposed replacement in `Planning` or `In-Progress` is insufficient. |
| `Abandoned` | The human explicitly cancels an unimplemented package (or an unimplemented proposed delta). Preserve its history. If code from an `In-Testing` or `Verified` package is already live, do not mark it `Abandoned`; retain its status until an authorized rollback or retirement delta reaches `In-Testing`. |

On every transition, update `spec.md` and `INDEX.md` together and append a dated entry in `## Approvals and lifecycle history`. Set `First entered In-Testing` to `YYYY-MM-DD` upon first entering `In-Testing` and retain that date forever. Preserve all prior approvals and test runs; a past approval does not cover new scope or verify a subsequent fix. Report environmental blockers honestly rather than inventing a passing run.

## Select the revision route before changing status

Inspect `First entered In-Testing`, `## Approvals and lifecycle history`, and `verification.md` **before** editing normative text. A reopened `In-Progress` or `Planning` package may already have reached testing. For imported packages lacking `First entered In-Testing`, infer it from history or record `Unknown` temporarily while in `Planning`/`In-Progress` and resolve it to `YYYY-MM-DD` (or `Never`) with the owner before promoting to `In-Testing` or `Verified` or altering requirement bodies.

- **Never reached testing (`First entered In-Testing: Never`):** Amend requirements in place when intent changes. Preserve existing `REQ-NNN` IDs for updated requirements; mint new IDs for distinct added requirements/criteria and never reuse retired IDs. Record the reason, reset affected gates to `UNCHECKED`, and return the package to `Planning` before updating derived plans.
- **Reached testing at least once (`First entered In-Testing: YYYY-MM-DD`):** Keep existing `REQ-NNN` statements and `AC-NNN-M` bodies byte-for-byte unchanged. Create a linked delta package in `Planning` for changed, added, or retired behavior, minting new repo-wide `REQ-NNN` IDs and recording `Previous contract`. Do not reset the parent's `First entered In-Testing` date or change the parent's status until activation rules apply.
- **Whole-package replacement:** Create a new package declaring `Replaces [<prior-feature>](../<prior-feature>/spec.md)` that covers all retained behavior as well as deliberate changes/removals. Do not mix whole-package `Replaces` with partial `Changes`/`Retires` against the same target.

Updating metadata headers, appending approval/history entries, and inserting `- Current contract:` annotations below a parent requirement heading does not violate frozen-body immutability. `ADR-NNN` entries use four states: `Proposed`, `Accepted`, `Superseded by ADR-NNN`, and `Abandoned`. Accepted ADR bodies remain historical; append a new `ADR-NNN` when a decision changes and update the old entry's state to `Superseded by ADR-NNN`.

## Related specifications and activation

Label cross-package links as `Proposed: Changes|Retires|Replaces [...]` while the delta or replacement is in `Planning` or `In-Progress`, and update to `Implemented: Changes|Retires|Replaces [...]` once it reaches `In-Testing`. A parent may list a `Proposed` delta under `Related specifications` without presenting it as the governing contract.

When a delta reaches `In-Testing`, update both packages: mark the relationship `Implemented`, and add a 1-hop `- Current contract:` bullet immediately below each affected parent requirement heading (pointing to `Changed by` or `Retired by` the delta requirement). When a chain of deltas modifies the same behavior (`Spec A/REQ-001` -> `Delta B/REQ-005` -> `Delta C/REQ-009`), `Delta C`'s `Changes:` or `Retires:` targets the currently governing requirement (`Delta B/REQ-005`), and when `Delta C` reaches `In-Testing`, update `- Current contract:` on **every prior ancestor in the chain** (`Spec A/REQ-001` and `Delta B/REQ-005`) to point 1-hop directly to `Delta C/REQ-009`.

A partially modified parent retains its `In-Testing` or `Verified` status for unaffected requirements. A whole-package replacement reaching `In-Testing` transitions its parent to `Superseded` in both `spec.md` and `INDEX.md`. If a proposed delta is cancelled before reaching `In-Testing`, mark the delta `Abandoned` and remove or mark its `Proposed` link abandoned; it never becomes the current contract. Retiring live behavior requires an attributable `Retires:` requirement mapped through design, tasks, and verification like any other requirement.

## Three defect cases

Classify the root cause, not merely where the failure surfaced. Distinct defects affecting separate requirements may be split. However, if an architectural failure on a previously-tested package (`First entered In-Testing` is set) also forces changing that requirement's observable contract or acceptance criteria (`Case 2 + Case 3` coupled), do **not** reopen the parent into `Planning` against a frozen unachievable criterion: record both the new `ADR-NNN` and the changed `REQ-NNN` together in a linked delta package (or whole-package replacement), keeping the parent in `In-Testing` or `Verified` for unaffected requirements.

### Case 1: implementation defect

Requirements and design remain right; code, tests, or delivered artifacts fail to satisfy them.

1. Keep `REQ`/`AC` bodies, accepted ADR bodies, and valid design unchanged. Mint zero new `REQ-NNN` IDs.
2. Within authorization to fix the defect, reopen the package to `In-Progress` in `spec.md` and `INDEX.md`, appending a lifecycle entry. Add an unchecked `- [ ]` reproducer/fix task citing existing `REQ`/`AC` IDs and update Gate 2 mappings. Valid Gate 1 evidence remains intact.
3. Reproduce the failure when feasible, implement the fix, and run checks. Append a new run in `verification.md`; never overwrite prior runs.
4. When all tasks and checks pass, return to `In-Testing` (preserving the original `First entered In-Testing` date). Obtain fresh real-world confirmation before promoting back to `Verified`.

### Case 2: design or architecture defect

Observable `REQ`/`AC` contracts remain achievable and right, but the chosen technical approach failed in practice.

1. Preserve `REQ`/`AC` bodies and IDs (mint zero new `REQ-NNN` IDs). Set the package to `Planning` in `spec.md` and `INDEX.md`, retaining `First entered In-Testing`.
2. Append a replacement `ADR-NNN` (marking the prior accepted choice `State: Superseded by ADR-NNN`) or refine a still-`Proposed` choice; reset affected Gate 1 and Gate 2 rows to `UNCHECKED`.
3. Re-validate Gate 1 in `decisions.md`, update `design.md`, `tasks.md`, and `verification.md` planned checks (preserving historical run logs), and re-validate Gate 2.
4. Confirm authorization if tradeoffs or scope changed materially, execute, and pass through `In-Testing` and `Verified` again.

### Case 3: missing or incorrect requirement

Observable behavior or acceptance criteria must change.

1. Pause affected work and check `First entered In-Testing` **before** editing status or text.
2. Amend a never-tested package in place (preserving IDs for updated requirements and minting new `REQ-NNN` IDs for distinct added requirements), or create a linked delta package for a previously-tested package (minting new `REQ-NNN` IDs for every changed, added, or retired requirement—unlike Case 1 and Case 2, which mint zero new requirement IDs).
3. Resolve material product questions with the owner, complete Gate 1, derive updated `design.md`, `tasks.md`, and `verification.md` plans, and complete Gate 2.
4. Execute within explicit authorization and apply parent activation updates only when the delta reaches `In-Testing`.

## Owner-deferred decisions

An explicit owner deferral (`[PROVISIONAL]`) permits design exploration while keeping its Gate 2 criteria and dependent tasks `BLOCKED`. Independent settled tasks may execute when authorized and all non-blocked Gate 2 rows pass.

- **When answered:** Record the owner's resolution, replace `[PROVISIONAL]` markers and deferred stubs with final observable criteria, and re-run affected Gate 1 and Gate 2 checks (via a linked delta if the package had already reached testing).
- **Descoping when settled work finishes first:** Because no package with `[PROVISIONAL]` or `BLOCKED` items may enter `In-Testing`, an owner who wants to ship completed settled requirements before answering a deferred `[PROVISIONAL]` requirement in a never-tested package may authorize splitting it out: either move the deferred requirement (retaining its allocated `REQ-NNN` ID) into a new `Planning` package, or drop it into `Non-goals` while permanently retiring its `REQ-NNN` ID without reuse; then remove its `BLOCKED` tasks and Gate 2 rows, re-validate Gate 1 and Gate 2, and advance the settled package to `In-Testing`.

## Out-of-band code drift

When manual commits or external changes cause live code to diverge from an `In-Testing` or `Verified` package, do not silently edit `spec.md` to match the code or overwrite the code without checking intent. Surface the exact discrepancy (`file:line` vs `REQ-NNN`/`AC-NNN-M`) to the owner and route as **Case 1** if code broke the intended contract, or **Case 3** (linked delta) if intended behavior changed.
